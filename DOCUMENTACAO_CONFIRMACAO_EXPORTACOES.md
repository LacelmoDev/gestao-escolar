Documentação: Confirmação de Matrícula e Exportações (PDF / XLSX)

Resumo das Correcções Realizadas
- Corrigi um bug em templates: vários links usavam o nome de url `confirmacao-matricula` (com hífen), enquanto a URL nomeada no `core/urls.py` é `confirmacao_matricula` (com underline). Atualizei `templates/home.html`.
- Criei templates que faltavam: `confirmacao_sucesso.html`, `confirmacao_estado.html` e `acesso_congelado.html`.
- Refatorei a view `confirmacao_matricula` para permitir visitantes não autenticados (removeu `@login_required`).
- Modifiquei o modelo `ConfirmacaoMatricula` para aceitar confirmações de visitantes:
  - Campo `aluno` agora é opcional (`null=True, blank=True`)
  - Adicionado campo `nome_completo` para visitantes que não têm perfil de aluno no sistema
- A view de confirmação também tenta mapear visitantes a um `Aluno` existente pelo `bi_numero` e/ou nome completo.
- Criada e aplicada migration: `0015_confirmacaomatricula_nome_completo_and_more`
- Executei testes automatizados — 4 testes passam localmente.
- Rodei `manage.py check` — identificadas recomendações de segurança (HSTS, DEBUG, SECRET_KEY) — são setting de deploy.

Funcionalidade: Confirmação de Matrícula (Refatorada)
- Endpoint (view): `confirmacao_matricula` (rota `/confirmacao-matricula/`).
- Agora permite VISITANTES não autenticados submeterem confirmações.
- Comportamento:
  1. Se aluno autenticado com perfil no sistema:
     - Sistema carrega dados da turma e calcula proxima classe automaticamente
     - Se 9ª classe, pede escolha de curso para II Ciclo
     - Preenche apenas foto, BI e email (dados pessoais já existem)
  2. Se visitante (não autenticado):
     - Formulário completo: nome completo, foto, BI, email
     - Não há cálculo automático de classe (default 10ª)
     - Registro criado sem usuário associado

- Fluxo de submissão:
  1. Validação de campos obrigatórios (foto, BI, email, e nome se visitante)
  2. Criação de `ConfirmacaoMatricula` com `status='EM_REVISAO'`
  3. Email automático enviado via `_email_confirmacao(..., 'EM_REVISAO')`
  4. Redirect para página de sucesso (`confirmacao_sucesso.html`)

- Emails automáticos:
  - Função `_email_confirmacao(confirmacao, tipo)` gera HTML rico
  - Tipos suportados: `EM_REVISAO`, `AGUARDANDO_PAGAMENTO`, `ATIVO`, `REJEITADO`
  - Requisito: `confirmacao.email` deve existir

- Modelos envolvidos:
  - `ConfirmacaoMatricula` em `academico/models.py`
  - Campos relevantes: `aluno` (FK, nullable), `nome_completo`, `ano_letivo`, `foto_rosto`, `bi_numero`, `email`, `classe_nova`, `curso_novo`, `status`
  - unique_together = ('aluno', 'ano_letivo') — impede duplicatas para alunos autenticados; visitantes não têm essa restrição

Permissões / Middleware relevantes
- `CongelamentoMiddleware` bloqueia alunos congelados em caminhos específicos (permite `/confirmacao-matricula/`, `/confirmacao-estado/`, `/acesso-congelado/`, etc.)
- A view `confirmacao_matricula` não requer autenticação (removida `@login_required`)
- A view `confirmacao_estado` requer autenticação (apenas para alunos logados)
- A página `acesso_congelado` exibe um aviso quando o aluno ainda está congelado e orienta para a submissão da confirmação.

Funcionalidade: Exportações (Admin e Professor)
- Requisitos:
  - Biblioteca para Excel: `openpyxl` (instale com `pip install openpyxl`).
  - Biblioteca para PDF: `xhtml2pdf` (instale com `pip install xhtml2pdf`) ou outra engine compatível.

- Rotas / Views:
  - Admin:
    - XLSX: `exportar_relatorio_excel` → `/relatorios/exportar/excel/` (requer `request.user.is_staff or request.user.is_admin_escola`).
    - PDF: `exportar_relatorio_pdf` → `/relatorios/exportar/pdf/` (mesma permissão).
  - Professor (relatório por turma):
    - XLSX: `exportar_relatorio_turma_excel` → `/professor/turma/<turma_id>/relatorio/excel/` (requer `request.user.is_professor` e `Atribuicao` válida).
    - PDF: `exportar_relatorio_turma_pdf` → `/professor/turma/<turma_id>/relatorio/pdf/` (mesmas verificações).

- Comportamento das exportações:
  - Excel (.xlsx): gera planilhas com abas separadas (Inscrições, Alunos por Turma, Frequência) usando `openpyxl`, aplica estilos básicos e entrega como `Content-Disposition: attachment`.
  - PDF: renderiza templates (`academico/relatorio_pdf.html` e `academico/relatorio_turma_pdf.html`) e passa o HTML para `xhtml2pdf.pisa.CreatePDF`, retornando o PDF como attachment.

Observações & Recomendações
- Segurança/Deploy: `manage.py check --deploy` levantou avisos (HSTS/HTTPS/SECRET_KEY/DEBUG). Ajuste `settings.py` em produção.
- Dependências: garanta que `openpyxl` e `xhtml2pdf` estejam no `requirements.txt` (ou instale manualmente no venv).
- Templates PDF: adicionadas `academico/relatorio_pdf.html` e `academico/relatorio_turma_pdf.html` para suportar exportação de relatórios em PDF.
- Testes: adicionei cobertura para exportação XLSX/PDF de admin e professor; os testes atuais passam.
- Visitantes sem conta: após submeter confirmação, visitantes não podem ver o estado (apenas alunos autenticados). Considere adicionar:
  - Email com link único para acessar estado
  - Query param com token de verificação
  - Sistema de "Claim" da confirmação ao registar conta

Alterações de Ficheiros
- `academico/models.py`: Campo `aluno` nullable, adicionado `nome_completo`
- `academico/views_confirmacao.py`: Refatorada view `confirmacao_matricula` sem `@login_required`, adicionada lógica para visitantes
- `templates/academico/confirmacao_form.html`: Adicionado campo de nome completo para visitantes, ajustado layout
- `templates/academico/confirmacao_sucesso.html`: NOVO — página de sucesso após submissão
- `templates/academico/confirmacao_estado.html`: NOVO — página de estado (apenas para alunos autenticados)
- `templates/academico/acesso_congelado.html`: NOVO — página exibida quando matrícula está congelada
- `templates/academico/relatorio_pdf.html`: NOVO — template de PDF para relatório admin
- `templates/academico/relatorio_turma_pdf.html`: NOVO — template de PDF para relatório de turma
- `academico/admin.py`: adicionadas ações em massa no admin de `Aluno` para congelar/descongelar os alunos selecionados
- `templates/home.html`: Corrigidos links de URL (confirmacao-matricula → confirmacao_matricula)
- `academico/migrations/0015_confirmacaomatricula_nome_completo_and_more.py`: NOVO — migration criada e aplicada
- `academico/tests_integration.py`: NOVO teste para exportações admin e professor

Próximos passos sugeridos (opcionais)
- Adicionar recuperação de estado para visitantes (usar token/email)
- Melhorar geração de PDF: considerar `WeasyPrint` para layouts CSS mais robustos
- Adicionar validação de email único por confirmação
- Sistema de notificação por SMS para visitantes (se disponível)
- Integração com painel de admin para revisar/aprovar confirmações de visitantes

