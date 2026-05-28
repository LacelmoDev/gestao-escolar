import re
import logging
import threading

import sib_api_v3_sdk
from django.conf import settings

logger = logging.getLogger("academico")


def _enviar_email_async(subject, message, from_email, recipient_list, html_message=None):
    """Envia email via Brevo API em background thread — não bloqueia o worker."""
    def _send():
        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = settings.EMAIL_HOST_PASSWORD

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )

            # Extrai só o email se vier no formato "Nome <email>"
            match = re.search(r'<(.+?)>', settings.DEFAULT_FROM_EMAIL)
            sender_clean = match.group(1) if match else settings.DEFAULT_FROM_EMAIL

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": r} for r in recipient_list],
                sender={"name": "Colégio Tarimba", "email": sender_clean},
                subject=subject,
                html_content=html_message or f"<p>{message}</p>",
                text_content=message,
            )

            api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email enviado via Brevo API para {recipient_list}")

        except Exception as e:
            logger.error(f"Erro ao enviar email para {recipient_list}: {e}")

    t = threading.Thread(target=_send, daemon=True)
    t.start()


def _html_base(titulo, subtitulo, corpo):
    """Template HTML base para todos os emails."""
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
      <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)">
        <div style="background:#E8621A;padding:20px;text-align:center;color:#fff">
          <h2 style="margin:0">Colégio Tarimba</h2>
          <p style="margin:5px 0 0;font-size:13px">{subtitulo}</p>
        </div>
        <div style="padding:30px">{corpo}</div>
        <div style="background:#f9f9f9;padding:15px;text-align:center;font-size:11px;color:#999;border-top:1px solid #eee">
          Sistema Académico Tarimba · C.E.P. J.M.F.D - Calumbo
        </div>
      </div>
    </body></html>
    """


def enviar_email_inscricao_recebida(inscricao):
    """Email 1 — enviado logo após o candidato submeter a inscrição."""
    if not inscricao.email:
        return

    corpo = f"""
      <p>Olá, <strong>{inscricao.nome_completo}</strong>,</p>
      <p>A sua inscrição foi recebida com sucesso e está em análise pela nossa secretaria.</p>
      <div style="background:#FFF3ED;border:1px solid #E8621A;border-radius:8px;padding:15px;margin:20px 0">
        <p style="margin:4px 0"><strong>Protocolo:</strong> #{inscricao.id:05d}</p>
        <p style="margin:4px 0"><strong>Curso:</strong> {inscricao.curso_pretendido}</p>
        <p style="margin:4px 0"><strong>Classe:</strong> {inscricao.classe_pretendida}ª Classe</p>
        <p style="margin:4px 0"><strong>Data:</strong> {inscricao.data_submissao.strftime('%d/%m/%Y às %H:%M')}</p>
      </div>
      <p>Aguarde o contacto da secretaria via WhatsApp ou email para confirmação dos dados.</p>
    """

    _enviar_email_async(
        subject=f"📋 Inscrição Recebida — Colégio Tarimba (#{inscricao.id:05d})",
        message=f"Olá {inscricao.nome_completo}, a sua inscrição #{inscricao.id:05d} foi recebida e está em análise.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[inscricao.email],
        html_message=_html_base("Inscrição Recebida", "A sua candidatura está em análise", corpo),
    )


def _enviar_notificacao_status(inscricao, tipo):
    """Emails 2 e 3 — notificações de mudança de estado (CONFIRMADO / REJEITADO)."""
    if not inscricao.email:
        logger.warning(f"Inscrição {inscricao.id} sem email — notificação ignorada.")
        return False

    if tipo == 'CONFIRMADO':
        assunto = "✅ Dados Confirmados — Dirija-se ao Colégio para Pagamento"
        corpo = f"""
          <p>Olá, <strong>{inscricao.nome_completo}</strong>,</p>
          <p>Os seus dados foram verificados e confirmados pela nossa secretaria.</p>
          <div style="background:#FFF3ED;border:1px solid #E8621A;border-radius:8px;padding:15px;margin:20px 0">
            <p style="margin:4px 0"><strong>Próximo passo:</strong> Dirija-se ao Colégio Tarimba para efectuar o pagamento da taxa de matrícula.</p>
            <p style="margin:8px 0 4px;font-size:13px;color:#666">Apresente o comprovativo PDF da inscrição ou este email.</p>
          </div>
          <p style="font-size:13px;color:#999">Após o pagamento, o seu acesso ao Portal do Aluno será activado.</p>
        """

    elif tipo == 'REJEITADO':
        assunto = "❌ Inscrição Não Aprovada — Colégio Tarimba"
        motivo = (
            f'<div style="background:#fff3f3;border-left:4px solid #e53e3e;padding:10px;margin:15px 0">'
            f'<p style="margin:0"><strong>Motivo:</strong> {inscricao.observacoes_adm}</p></div>'
            if inscricao.observacoes_adm else ''
        )
        corpo = f"""
          <p>Olá, <strong>{inscricao.nome_completo}</strong>,</p>
          <p>Após análise, não foi possível aprovar a sua inscrição para o ano lectivo 2025/2026.</p>
          {motivo}
          <p>Para mais informações, contacte a secretaria do colégio pelo <strong>928 098 791</strong>.</p>
        """

    else:
        logger.warning(f"Tipo de notificação desconhecido: {tipo}")
        return False

    _enviar_email_async(
        subject=assunto,
        message=f"Olá {inscricao.nome_completo}, o estado da sua inscrição foi actualizado: {tipo}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[inscricao.email],
        html_message=_html_base("Actualização da Inscrição", "Colégio Tarimba", corpo),
    )
    return True


def _enviar_email_boas_vindas(inscricao, usuario, senha_temp, turma, numero_processo):
    """Email 4 — boas-vindas com credenciais de acesso ao Portal do Aluno."""
    if not usuario.email:
        logger.warning(f"Utilizador {usuario.username} sem email — boas-vindas ignoradas.")
        return False

    turma_info = str(turma) if turma else "a ser atribuída"

    corpo = f"""
      <p>Olá, <strong>{inscricao.nome_completo}</strong>,</p>
      <p>A tua matrícula foi concluída com sucesso! Aqui estão os teus dados de acesso ao Portal do Aluno:</p>
      <div style="background:#FFF3ED;border:1px solid #E8621A;border-radius:8px;padding:15px;margin:20px 0">
        <p style="margin:5px 0"><strong>Utilizador:</strong> {usuario.username}</p>
        <p style="margin:5px 0"><strong>Senha Temporária:</strong>
          <code style="background:#f0f0f0;padding:2px 6px;border-radius:4px;color:#E8621A;font-size:15px">{senha_temp}</code>
        </p>
      </div>
      <div style="font-size:14px;color:#555;background:#f9f9f9;padding:12px;border-left:4px solid #E8621A;margin-bottom:20px">
        <p style="margin:3px 0"><strong>Nº Processo:</strong> {numero_processo}</p>
        <p style="margin:3px 0"><strong>Curso:</strong> {inscricao.curso_pretendido}</p>
        <p style="margin:3px 0"><strong>Turma:</strong> {turma_info}</p>
      </div>
      <p style="font-size:13px;color:#e53e3e">⚠️ Por segurança, altere a sua senha no primeiro acesso.</p>
    """

    _enviar_email_async(
        subject="🎓 Bem-vindo(a) ao Portal do Aluno — Colégio Tarimba",
        message=f"Olá {inscricao.nome_completo}, o teu login é {usuario.username} e a senha temporária é {senha_temp}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        html_message=_html_base("Bem-vindo(a)!", "Acesso ao Portal Académico", corpo),
    )
    return True