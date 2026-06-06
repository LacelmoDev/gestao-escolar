from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.db.models import Count
from xhtml2pdf import pisa
import logging

from .models import Nota, Aluno, Presenca, Inscricao, Notificacao
from .forms import InscricaoForm, PerfilAlunoForm
from .utils import enviar_email_inscricao_recebida
from .services import get_ano_letivo_atual
from escola.models import Professor, Turma, Atribuicao, Disciplina

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'home.html')


def inscrever(request):
    if request.method == 'POST':
        referer = request.META.get('HTTP_REFERER', 'N/A')
        origin = request.META.get('HTTP_ORIGIN', 'N/A')
        host = request.get_host()
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', 'N/A')
        csrf_cookie = request.COOKIES.get('csrftoken', 'N/A')[:20] if request.COOKIES.get('csrftoken') else 'N/A'

        logger.info(f"POST /inscrever/ - Diagnóstico CSRF:")
        logger.info(f"  Referer: {referer}")
        logger.info(f"  Origin: {origin}")
        logger.info(f"  Host: {host}")
        logger.info(f"  X-Forwarded-Proto: {forwarded_proto}")
        logger.info(f"  CSRF Cookie (primeiros 20 chars): {csrf_cookie}")
        logger.info(f"  Request META keys (CSRF-related): {[k for k in request.META.keys() if 'CSRF' in k or 'csrf' in k]}")

        form = InscricaoForm(request.POST, request.FILES)
        if form.is_valid():
            inscricao = form.save()
            logger.info(f"✓ Inscrição criada com sucesso: {inscricao.id}")
            
            # Criar notificação para o admin
            Notificacao.objects.create(
                inscricao=inscricao,
                tipo='INSCRICAO'
            )
            logger.info(f"✓ Notificação criada para inscrição: {inscricao.id}")
            
            enviar_email_inscricao_recebida(inscricao)
            return render(request, 'academico/inscricao_sucesso.html', {'inscricao': inscricao})
        else:
            logger.warning(f"✗ Erro de validação do formulário: {form.errors}")
            messages.error(request, "Erro ao processar inscrição. Verifique os dados.")
    else:
        form = InscricaoForm()
    return render(request, 'academico/form_inscricao.html', {'form': form})


@login_required
def dashboard(request):
    try:
        aluno = Aluno.objects.select_related('turma').get(usuario=request.user)
        anos_disponiveis = Nota.objects.filter(aluno=aluno).values_list(
            'aluno__turma__ano_letivo', flat=True
        ).distinct().order_by('-aluno__turma__ano_letivo')

        ano_atual_aluno = aluno.turma.ano_letivo if aluno.turma else get_ano_letivo_atual()
        ano_selecionado = request.GET.get('ano')

        if not ano_selecionado:
            ano_selecionado = ano_atual_aluno
        else:
            ano_selecionado = int(ano_selecionado)

        notas = Nota.objects.filter(
            aluno=aluno,
            aluno__turma__ano_letivo=ano_selecionado
        ).select_related('disciplina')

        presencas_aluno = Presenca.objects.filter(
            aluno=aluno,
            esta_presente=False,
            data__year=ano_selecionado
        ).select_related('disciplina')

        faltas_justificadas = presencas_aluno.filter(justificada=True).count()
        faltas_analise = presencas_aluno.filter(
            justificada=False
        ).exclude(documento_justificativo__in=['', None]).count()
        faltas_nao_justificadas = presencas_aluno.filter(
            justificada=False,
            documento_justificativo__in=['', None]
        ).count()

        context = {
            'aluno': aluno,
            'notas': notas,
            'faltas_justificadas': faltas_justificadas,
            'faltas_nao_justificadas': faltas_nao_justificadas,
            'faltas_analise': faltas_analise,
            'todas_faltas': presencas_aluno.order_by('-data'),
            'anos_disponiveis': anos_disponiveis,
            'ano_selecionado': ano_selecionado
        }

    except Aluno.DoesNotExist:
        context = {'aluno': None}

    return render(request, 'academico/dashboard.html', context)


@login_required
def justificar_falta(request):
    if request.method == 'POST':
        presenca_id = request.POST.get('presenca_id')
        presenca = get_object_or_404(Presenca, id=presenca_id, aluno__usuario=request.user)

        if request.FILES.get('documento'):
            presenca.documento_justificativo = request.FILES.get('documento')
            presenca.observacao_justificativa = request.POST.get('observacao')
            presenca.save()
            messages.info(request, "Justificativa enviada para análise do professor.")
        else:
            messages.error(request, "É necessário anexar um documento.")

    return redirect('dashboard')


@login_required
def perfil_aluno(request):
    aluno = get_object_or_404(Aluno, usuario=request.user)
    inscricao = Inscricao.objects.filter(bi_numero=aluno.usuario.username).first()

    if request.method == 'POST':
        form = PerfilAlunoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil')
    else:
        form = PerfilAlunoForm(instance=request.user)

    return render(request, 'academico/perfil.html', {
        'aluno': aluno,
        'inscricao': inscricao,
        'form': form
    })


@login_required
def dashboard_professor(request):
    if not request.user.is_professor:
        raise PermissionDenied

    try:
        professor = Professor.objects.get(usuario=request.user)
        turmas = Turma.objects.filter(grade_curricular__professor=professor).distinct()
        disciplinas_ativas = Disciplina.objects.filter(atribuicao__professor=professor).distinct()

        pendentes = Presenca.objects.filter(
            disciplina__in=disciplinas_ativas,
            esta_presente=False,
            justificada=False
        ).exclude(documento_justificativo__in=['', None]).select_related('aluno__usuario', 'disciplina')

        return render(request, 'academico/professor_dashboard.html', {
            'professor': professor,
            'turmas': turmas,
            'pendentes': pendentes,
            'total_pendentes': pendentes.count()
        })
    except Professor.DoesNotExist:
        messages.warning(request, "Seu perfil de professor ainda não foi configurado.")
        return render(request, 'academico/professor_dashboard.html', {'professor': None})


@login_required
def turma_detalhe(request, turma_id):
    if not request.user.is_professor:
        raise PermissionDenied

    turma = get_object_or_404(Turma, id=turma_id)
    alunos = Aluno.objects.filter(turma=turma).order_by('usuario__first_name')
    professor = get_object_or_404(Professor, usuario=request.user)
    atribuicoes = Atribuicao.objects.filter(professor=professor, turma=turma).select_related('disciplina')
    disciplinas = [a.disciplina for a in atribuicoes]

    return render(request, 'academico/turma_detalhe.html', {
        'turma': turma,
        'alunos': alunos,
        'disciplinas': disciplinas
    })


@login_required
def notas_aluno_json(request, aluno_id):
    """Retorna as notas de um aluno em JSON para o modal de visualização no painel do professor."""
    if not request.user.is_professor:
        raise PermissionDenied

    professor = get_object_or_404(Professor, usuario=request.user)
    turma_id = request.GET.get('turma')

    # Garante que o professor tem atribuição nesta turma
    if turma_id and not Atribuicao.objects.filter(professor=professor, turma_id=turma_id).exists():
        return JsonResponse({'erro': 'Acesso negado'}, status=403)

    aluno = get_object_or_404(Aluno, id=aluno_id)
    notas = Nota.objects.filter(aluno=aluno).select_related('disciplina').order_by('disciplina__nome', 'trimestre')

    from decimal import Decimal
    dados = []
    for n in notas:
        media = ((n.mac + n.npp + n.npt) / Decimal('3')).quantize(Decimal('0.1'))
        dados.append({
            'disciplina': n.disciplina.nome,
            'trimestre': n.trimestre,
            'mac': float(n.mac),
            'npp': float(n.npp),
            'npt': float(n.npt),
            'media': float(media),
        })

    return JsonResponse({'notas': dados, 'aluno': aluno.usuario.get_full_name()})


@login_required
def lancar_nota_rapida(request):
    if request.method == 'POST' and request.user.is_professor:
        aluno_id = request.POST.get('aluno_id')
        disciplina_id = request.POST.get('disciplina_id')
        turma_id = request.POST.get('turma_id')

        professor = get_object_or_404(Professor, usuario=request.user)

        if not Atribuicao.objects.filter(professor=professor, disciplina_id=disciplina_id, turma_id=turma_id).exists():
            messages.error(request, "Acesso negado: Você não leciona esta disciplina nesta turma.")
            return redirect('professor_dashboard')

        # Validação backend — notas devem estar entre 0 e 20
        try:
            mac = float(request.POST.get('mac', 0))
            npp = float(request.POST.get('npp', 0))
            npt = float(request.POST.get('npt', 0))
        except (ValueError, TypeError):
            messages.error(request, "Valores de nota inválidos.")
            return redirect('turma_detalhe', turma_id=turma_id)

        if not all(0 <= v <= 20 for v in [mac, npp, npt]):
            messages.error(request, "Notas devem estar entre 0 e 20.")
            return redirect('turma_detalhe', turma_id=turma_id)

        Nota.objects.update_or_create(
            aluno_id=aluno_id,
            disciplina_id=disciplina_id,
            trimestre=request.POST.get('trimestre'),
            defaults={'mac': mac, 'npp': npp, 'npt': npt}
        )
        messages.success(request, "Nota atualizada com sucesso!")
        return redirect('turma_detalhe', turma_id=turma_id)
    return redirect('professor_dashboard')


@login_required
def marcar_falta_rapida(request):
    if request.method == 'POST' and request.user.is_professor:
        aluno_id = request.POST.get('aluno_id')
        turma_id = request.POST.get('turma_id')

        Presenca.objects.create(
            aluno_id=aluno_id,
            disciplina_id=request.POST.get('disciplina_id'),
            data=request.POST.get('data'),
            esta_presente=False,
            justificada=False
        )
        messages.warning(request, "Falta registrada com sucesso.")
        return redirect('turma_detalhe', turma_id=turma_id)
    return redirect('professor_dashboard')


@login_required
def aprovar_justificativa(request, presenca_id):
    if not request.user.is_professor:
        raise PermissionDenied

    presenca = get_object_or_404(Presenca, id=presenca_id)
    presenca.justificada = True
    presenca.save()
    messages.success(request, f"Justificativa de {presenca.aluno.usuario.get_full_name()} aprovada!")
    return redirect('professor_dashboard')


@login_required
def rejeitar_justificativa(request, presenca_id):
    if not request.user.is_professor:
        raise PermissionDenied

    presenca = get_object_or_404(Presenca, id=presenca_id)
    presenca.documento_justificativo = None
    presenca.observacao_justificativa = ""
    presenca.save()
    messages.warning(request, f"A justificativa de {presenca.aluno.usuario.get_full_name()} foi recusada.")
    return redirect('professor_dashboard')


@login_required
def redirecionar_apos_login(request):
    if request.user.is_professor:
        return redirect('professor_dashboard')
    elif request.user.is_aluno:
        return redirect('dashboard')
    else:
        return redirect('/tarimba-painel-2026/')


def precario(request):
    return render(request, 'academico/precario.html')


def gerar_pdf_inscricao(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id)

    template_path = 'academico/pdf_inscricao.html'
    context = {'inscricao': inscricao}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Inscricao_{inscricao.bi_numero}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF <pre>' + html + '</pre>')

    return response
