# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Avg, Count
from django.db import transaction

class EmailUserManager(BaseUserManager):
    def create_user(self, email, password=None, primeiro_nome=None, ultimo_nome=None, cpf = None, **kwargs):
        
        if not email:
            raise ValueError('Email é obrigatório.')

        if not primeiro_nome:
            raise ValueError('Primeiro Nome é obrigatório.')

        if not ultimo_nome:
            raise ValueError('Ultimo Nome é obrigatório.')

        if not cpf:
            raise ValueError('CPF é obrigatório.')

        email = self.normalize_email(email)
        user = self.model(email=email, primeiro_nome=primeiro_nome, ultimo_nome=ultimo_nome, cpf = cpf, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, primeiro_nome, ultimo_nome, cpf):
        user = self.create_user(email, password=password, primeiro_nome=primeiro_nome, ultimo_nome=ultimo_nome, cpf=cpf)
        user.administrador = True
        user.save(using=self._db)
        return user

class Usuario(PermissionsMixin, AbstractBaseUser):
    cpf = models.CharField(
        max_length=14,
        blank=False,
        help_text=_('O campo CPF é obriagatório.'),
        unique = True,)
    email = models.EmailField(
        verbose_name=_('Email'),
        max_length = 60,
        unique=True,
        help_text=_('O campo Email é obrigatório.'),)
    primeiro_nome = models.CharField(
        verbose_name=_('Nome'),
        max_length=50,
        blank=False,
        help_text=_('O campo Nome é obrigatório.'),)
    ultimo_nome = models.CharField(
        verbose_name=_('Sobrenome'),
        max_length=50,
        blank=False,
        help_text=_('O campo Sobrenome é obrigatório.'),)
    ativo = models.BooleanField(default=True)
    administrador = models.BooleanField(default=False)
    conta_publica = models.BooleanField(default=False)
    formacao = models.CharField(max_length=150,null = True)
    profissao = models.CharField(max_length=150,null = True)
    data_cadastro = models.DateTimeField(default=timezone.now)

    objects = EmailUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['primeiro_nome','ultimo_nome','cpf']

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')

    def __str__(self):
        return self.primeiro_nome +" "+ self.ultimo_nome

    def obter_nome_completo(self):
        return self.primeiro_nome +" "+ self.ultimo_nome

    def obter_nome_exibicao(self):
        if self.conta_publica:
            return self.obter_nome_completo()
        else:
            return "Usuário Anônimo" 

    def obter_profissao(self):
        if not self.profissao:
            return None
        else:
            return self.profissao        

    @staticmethod
    def obter_usuario(id):
        return Usuario.objects.get(pk=id)

    @staticmethod
    def verificar_email_valido(email,primeiro_nome):
        return Usuario.objects.filter(email=email).exclude(primeiro_nome=primeiro_nome).count()

    @staticmethod
    def verificar_cpf_valido(cpf,primeiro_nome):
        return Usuario.objects.filter(cpf=cpf).exclude(primeiro_nome=primeiro_nome).count()

    def adicionar(self):
        self.ativo = False
        self.save()
    
    def ativar_conta(self):
        self.ativo = True
        self.save()

    def enviar_email(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    def has_module_perms(self, app_label):
        "O usuário tem permissão para visualizar o app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def has_perm(self, perm, obj=None):
        "O usuário possui uma permissão específica?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "O usuário é um administrador?"
        return self.administrador

    @property
    def is_superuser(self):
        return self.administrador

    @property
    def is_active(self):
        return self.ativo

class Linguagem(models.Model):
    nome = models.CharField(max_length=60)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    
    def __str__(self):
        return self.nome

    @staticmethod
    def obter_linguagens_minimo_um_framework():
        return Linguagem.objects.annotate(num_frameworks=Count('framework')).filter(num_frameworks__gt=0).all().order_by('nome')
    
    @staticmethod
    def obter_frameworks_linguagem(id):
        return Linguagem.objects.filter(id=id).first().framework_set.all().order_by('nome')

    @staticmethod
    def verificar_nome(nome):
        return Linguagem.objects.filter(nome=nome).first()
    
    @staticmethod
    def obter_linguagens():
        return Linguagem.objects.all().order_by('nome')

    @staticmethod
    def obter_linguagem(id):
        return Linguagem.objects.get(id=id)

    @staticmethod
    def obter_top10_mais_frameworks():
        return Linguagem.objects.raw('''SELECT 
                                            l.id
                                            ,l.nome
                                            ,count(f) as total_fram
                                        FROM public.wofapp_linguagem as l
                                        LEFT JOIN public.wofapp_framework f on f.linguagem_id = l.id
                                        GROUP BY l.id
                                                ,l.nome
                                        ORDER BY total_fram DESC
                                        LIMIT 10 
                                    ''')

    @staticmethod
    def adicionar(nome,user_id):
        linguagem = Linguagem(
            nome=nome,
            usuario_id=user_id,
        ) 
        linguagem.save()

    @staticmethod
    def obter_nome_denunciado(id):
        l = Linguagem.objects.get(id=id)
        return l.nome

class Framework(models.Model):
    nome = models.CharField(max_length=60)
    linguagem = models.ForeignKey(Linguagem, on_delete=models.CASCADE, null = False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    favoritado_por = models.ManyToManyField(Usuario, blank=True, related_name="favoritado_por")

    def __str__(self):
        return self.nome

    @staticmethod
    def obter_framework(id):
        return Framework.objects.get(id=id)

    @staticmethod
    def verificar_nome(nome):
        return Framework.objects.filter(nome=nome).first()

    @staticmethod
    def buscar_por_nome(nome):
        return Framework.objects.filter(nome__iexact=nome).first()

    @staticmethod
    def obter_top10_constribuicoes():
        return Framework.objects.raw('''SELECT
                                            fram.id
                                            ,fram.nome
                                            ,(count(distinct v.id) + count(distinct fu.id) +
                                            count(distinct h.id) + count(distinct o.id) + 
                                            count(distinct l.id) + count(distinct c.id) +
                                            count(distinct vo.id))
                                            as total_contribuicoes
                                        FROM public.wofapp_framework as fram
                                        LEFT JOIN public.wofapp_versao v on v.framework_id = fram.id
                                        LEFT JOIN public.wofapp_funcionalidade fu on fu.versao_id = v.id
                                        LEFT JOIN public.wofapp_helloworld h on h.versao_id = v.id
                                        LEFT JOIN public.wofapp_opiniao o on o.versao_id = v.id
                                        LEFT JOIN public.wofapp_link l on l.framework_id = fram.id
                                        LEFT JOIN public.wofapp_comentario c on c.framework_id = fram.id
                                        LEFT JOIN public.wofapp_voto vo on vo.link_id = l.id
                                        GROUP BY fram.id
                                                ,fram.nome
                                        ORDER BY total_contribuicoes DESC
                                        LIMIT 10
                                    ''')

    @staticmethod
    def adicionar(nome,lg_id,user_id):
        fram = Framework(
            nome = nome,
            linguagem_id = lg_id,
            usuario_id = user_id,
        ) 
        fram.save()

    @staticmethod
    def adicionar_favorito(id,user_id):
        with transaction.atomic():
            fram = Framework.objects.select_for_update().get(id=id)
            user = Usuario.objects.get(id=user_id)
            fram.favoritado_por.add(user)
            fram.save()

    @staticmethod
    def excluir_favorito(id,user_id):
        with transaction.atomic():
            fram = Framework.objects.select_for_update().get(id=id)
            user = Usuario.objects.get(id=user_id)
            fram.favoritado_por.remove(user)
            fram.save()

    @staticmethod
    def obter_nome_denunciado(id):
        f = Framework.objects.get(id=id)
        return f.nome

class Versao(models.Model):
    numero = models.DecimalField(default=0, max_digits=10, decimal_places=3)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, null = False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)

    def __str__(self):
        return str(self.numero) + ' ('+ str(self.framework.nome) +')'

    @staticmethod
    def obter_versao(id):
        return Versao.objects.get(id=id)

    @staticmethod
    def verificar_numero(numero, fm_id):
        return Versao.objects.filter(numero=numero,framework_id=fm_id).first()

    @staticmethod
    def adicionar(numero,fram_id,user_id):
        versao = Versao(
            numero = numero,
            framework_id = fram_id,
            usuario_id = user_id,
        ) 
        versao.save() 

    @staticmethod
    def editar(numero, vs_id, user_id):
        with transaction.atomic():
            versao = Versao.objects.select_for_update().get(id=vs_id)
            versao.numero = numero
            versao.usuario_id = user_id
            versao.save() 

class Helloworld(models.Model):
    codigo_exemplo = models.CharField(max_length=50000)
    descricao = models.CharField(max_length=50000)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    versao = models.ForeignKey(Versao, on_delete=models.CASCADE, null = False)

    def __str__(self):
        return self.descricao

    @staticmethod
    def adicionar(descricao,codigo_exemplo,user_id,vs_id):
        hello = Helloworld(
            descricao = descricao,
            codigo_exemplo = codigo_exemplo,
            usuario_id = user_id,
            versao_id = vs_id
        ) 
        hello.save()

class Funcionalidade(models.Model):
    descricao = models.CharField(max_length=5000)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    versao = models.ForeignKey(Versao, on_delete=models.CASCADE, null = False)

    def __str__(self):
        return self.descricao

    @staticmethod
    def adicionar(descricao,user_id,vs_id):
        fun = Funcionalidade(
            descricao=descricao,
            usuario_id=user_id,
            versao_id =vs_id
        ) 
        fun.save()

    @staticmethod
    def editar(desc, fun_id, user_id):
        with transaction.atomic():
            fun = Funcionalidade.objects.select_for_update().get(id=fun_id)
            fun.descricao = desc
            fun.usuario_id = user_id
            fun.save() 

class Opiniao(models.Model):
    texto = models.CharField(max_length=1000)
    eh_favoravel = models.BooleanField(default=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    versao = models.ForeignKey(Versao, on_delete=models.CASCADE, null = False)

    def __str__(self):
        return self.texto  

    @staticmethod
    def obter_texto_denunciado(id):
        o = Opiniao.objects.get(id=id)
        return o.texto

    @staticmethod
    def adicionar(texto,eh_favoravel,user_id,vs_id):
        op = Opiniao(
            texto=texto,
            eh_favoravel=eh_favoravel,
            usuario_id=user_id,
            versao_id =vs_id
        ) 
        op.save()

    @staticmethod
    def editar(texto, op_id, user_id):
        with transaction.atomic():
            opiniao = Opiniao.objects.select_for_update().get(id=op_id)
            opiniao.texto = texto
            opiniao.usuario_id = user_id
            opiniao.save() 

class Link(models.Model):
    caminho = models.CharField(max_length=800)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, null = False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)

    def __str__(self):
        return self.caminho

    @staticmethod
    def adicionar(caminho,user_id,fm_id):
        link = Link(
            caminho=caminho,
            usuario_id=user_id,
            framework_id=fm_id
        ) 
        link.save()

    @staticmethod
    def editar(caminho, li_id, user_id):
        with transaction.atomic():
            link = Link.objects.select_for_update().get(id=li_id)
            link.caminho = caminho
            link.usuario_id = user_id
            link.voto_set.all().delete()
            link.save() 

class Comentario(models.Model):
    texto = models.CharField(max_length=1000)
    data = models.DateTimeField(default=timezone.now)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, null = False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    respostas = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.texto

    @staticmethod
    def obter_texto_denunciado(id):
        c = Comentario.objects.get(id=id)
        return c.texto

    @staticmethod
    def adicionar(texto,fm_id,user_id):
        coment = Comentario(
            texto=texto,
            framework_id=fm_id,
            usuario_id=user_id
        )
        coment.save()   

    @staticmethod
    def adicionar_resposta(cm_id,texto,fm_id,user_id):
        with transaction.atomic():
            coment = Comentario.objects.select_for_update().get(id=cm_id)
            coment.comentario_set.create(
                texto=texto,
                framework_id= fm_id,
                usuario_id=user_id
                )

    @staticmethod
    def excluir(rs_id):
        with transaction.atomic():
            coment = Comentario.objects.select_for_update().get(id=rs_id)
            coment.delete()

class Voto(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE, null = False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)

    @staticmethod
    def verifica_voto(li_id,user_id):
        return Voto.objects.filter(link_id=li_id,usuario_id=user_id).first()

    @staticmethod
    def adicionar(li_id,user_id):
        voto = Voto(
            link_id=li_id,
            usuario_id=user_id
        )
        voto.save()   

class Denuncia(models.Model):
    data = models.DateTimeField(default=timezone.now)
    motivo = models.CharField(max_length=1000)
    resolvida = models.BooleanField(default=False)
    quem_denunciou = models.ForeignKey(Usuario, on_delete=models.CASCADE, null = False)
    linguagem = models.ForeignKey(Linguagem, on_delete=models.SET_NULL, blank=True, null=True)
    framework = models.ForeignKey(Framework, on_delete=models.SET_NULL, blank=True, null=True)
    opiniao = models.ForeignKey(Opiniao, on_delete=models.SET_NULL, blank=True, null=True)
    Comentario = models.ForeignKey(Comentario, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.motivo

    @staticmethod
    def denunciar_comentario(motivo,cm_id,user_id):
        de = Denuncia(
            motivo=motivo,
            quem_denunciou_id=user_id,
            Comentario_id=cm_id
        )
        de.save()   

    @staticmethod
    def denunciar_opiniao(motivo,op_id,user_id):
        de = Denuncia(
            motivo=motivo,
            quem_denunciou_id=user_id,
            opiniao_id=op_id
        )
        de.save()

    @staticmethod
    def verifica_denuncia_comentario(cm_id,user_id):
        return Denuncia.objects.filter(Comentario_id=cm_id,quem_denunciou_id=user_id).first()

    @staticmethod
    def verifica_denuncia_opiniao(op_id,user_id):
        return Denuncia.objects.filter(opiniao_id=op_id,quem_denunciou_id=user_id).first()   
