from django.contrib import admin
from .models import Curso, Turma, Disciplina, Professor, Atribuicao, GradeCurricular

# adicionar disciplinas diretamente dentro do Curso
class GradeCurricularInline(admin.TabularInline):
    model = GradeCurricular
    extra = 1

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'tem_prova_semestral')
    list_filter = ('tipo',)
    inlines = [GradeCurricularInline] 

@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'obrigatoria')
    search_fields = ('nome',)
    

@admin.register(GradeCurricular)
class GradeCurricularAdmin(admin.ModelAdmin):
    list_display = ('curso', 'classe', 'disciplina')
    list_filter = ('curso', 'classe')
    search_fields = ('disciplina__nome',)

@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('get_classe_display', 'nome', 'curso', 'turno', 'vagas')
    list_filter = ('classe', 'turno', 'curso')

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('get_nome', 'especialidade')
    filter_horizontal = ('disciplinas_habilitadas',)

    def get_nome(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username
    get_nome.short_description = 'Nome do Professor'

@admin.register(Atribuicao)
class AtribuicaoAdmin(admin.ModelAdmin):
    list_display = ('professor', 'disciplina', 'turma')
    list_filter = ('turma', 'professor')