import logging
from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

def pagina_404(request, exception):
    try:
        logger.warning(
            f"404 — Página não encontrada: {request.path} "
            f"| Utilizador: {request.user} "
            f"| Excepção: {exception}"
        )
        return render(request, '404.html', status=404)
    except Exception:
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound('<h1>404 - Página não encontrada</h1>')


def enviar_email_inscricao(inscricao):
    """
    Envia e-mail ao candidato quando o estado da inscrição muda.
    Chamar esta função nas views de aprovação/rejeição do admin.

    Uso:
        from academico.views_extras import enviar_email_inscricao
        # depois de mudar o status da inscrição:
        enviar_email_inscricao(inscricao)
    """
    if not inscricao.email:
        logger.info(f"Inscrição {inscricao.id}: sem e-mail, notificação ignorada.")
        return

    mensagens = {
        'CONFIRMADO': {
            'assunto': '✅ Inscrição Confirmada — Colégio Tarimba 3',
            'intro': 'A sua inscrição foi confirmada pela secretaria.',
            'detalhe': 'Por favor, proceda ao pagamento da propina e submeta o comprovativo no sistema para concluir a matrícula.',
            'cor': '#2ECC71',
        },
        'PAGO': {
            'assunto': '🎉 Matrícula Concluída — Colégio Tarimba 3',
            'intro': 'A sua matrícula foi concluída com sucesso!',
            'detalhe': 'Pode aceder ao sistema com as credenciais que lhe serão fornecidas pela secretaria.',
            'cor': '#4C9BE8',
        },
        'REJEITADO': {
            'assunto': '❌ Inscrição Não Aprovada — Colégio Tarimba 3',
            'intro': 'Lamentamos informar que a sua inscrição não foi aprovada.',
            'detalhe': inscricao.observacoes_adm or 'Por favor, contacte a secretaria do colégio para mais informações.',
            'cor': '#E74C3C',
        },
        'PENDENTE': {
            'assunto': '📋 Inscrição Recebida — Colégio Tarimba 3',
            'intro': 'A sua inscrição foi recebida com sucesso!',
            'detalhe': 'A secretaria irá analisar os seus dados e documentos. Acompanhe o estado pelo sistema.',
            'cor': '#F39C12',
        },
    }

    info = mensagens.get(inscricao.status)
    if not info:
        return
    
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #fff;
                  border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

        <!-- Cabeçalho colorido -->
        <div style="background: {info['cor']}; padding: 24px; text-align: center;">
          <h2 style="color: #fff; margin: 0; font-size: 20px;">Colégio Tarimba 3</h2>
          <p style="color: rgba(255,255,255,0.9); margin: 4px 0 0; font-size: 14px;">
            Sistema de Gestão Académica
          </p>
        </div>

        <!-- Corpo -->
        <div style="padding: 28px 32px;">
          <p style="font-size: 16px; color: #333;">Caro(a) <strong>{inscricao.nome_completo}</strong>,</p>
          <p style="font-size: 15px; color: #555;">{info['intro']}</p>
          <div style="background: #f8f9fa; border-left: 4px solid {info['cor']};
                      padding: 12px 16px; border-radius: 4px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #444;">{info['detalhe']}</p>
          </div>

          <!-- Dados da inscrição -->
          <table style="width: 100%; font-size: 14px; color: #555; margin-top: 16px;">
            <tr>
              <td style="padding: 4px 0; color: #888;">Número de B.I.:</td>
              <td style="padding: 4px 0;"><strong>{inscricao.bi_numero}</strong></td>
            </tr>
            <tr>
              <td style="padding: 4px 0; color: #888;">Curso pretendido:</td>
              <td style="padding: 4px 0;">{inscricao.curso_pretendido}</td>
            </tr>
            <tr>
              <td style="padding: 4px 0; color: #888;">Classe:</td>
              <td style="padding: 4px 0;">{inscricao.get_classe_pretendida_display()}</td>
            </tr>
            <tr>
              <td style="padding: 4px 0; color: #888;">Estado actual:</td>
              <td style="padding: 4px 0;">
                <span style="background: {info['cor']}; color: #fff;
                             padding: 2px 10px; border-radius: 12px; font-size: 13px;">
                  {inscricao.get_status_display()}
                </span>
              </td>
            </tr>
          </table>
        </div>

        <!-- Rodapé -->
        <div style="background: #f8f9fa; padding: 16px 32px; text-align: center;
                    border-top: 1px solid #eee;">
          <p style="margin: 0; font-size: 12px; color: #aaa;">
            Colégio Tarimba 3 &mdash; Sistema de Gestão Académica<br>
            Este é um e-mail automático. Por favor, não responda a este endereço.
          </p>
        </div>

      </div>
    </body>
    </html>
    """

    # Corpo em texto simples (fallback)
    corpo_texto = (
        f"Caro(a) {inscricao.nome_completo},\n\n"
        f"{info['intro']}\n\n"
        f"{info['detalhe']}\n\n"
        f"B.I.: {inscricao.bi_numero}\n"
        f"Curso: {inscricao.curso_pretendido}\n"
        f"Estado: {inscricao.get_status_display()}\n\n"
        f"Colégio Tarimba 3 — Sistema de Gestão Académica"
    )

    try:
        send_mail(
            subject=info['assunto'],
            message=corpo_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inscricao.email],
            html_message=corpo_html,
            fail_silently=False,
        )
        logger.info(f"E-mail enviado para {inscricao.email} — Estado: {inscricao.status}")
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail para {inscricao.email}: {e}")
