"""
Middleware para debug de CSRF em produção.
Log detalhado de POST requests para diagnóstico de erros 403.
"""
import logging

logger = logging.getLogger(__name__)


class CSRFDebugMiddleware:
    """
    Middleware que loga informações detalhadas de POST requests.
    Útil para diagnosticar erros CSRF 403 em produção.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.method == 'POST':
            self._log_post_details(request)
        
        response = self.get_response(request)
        
        # Log se a resposta foi 403 (CSRF fail)
        if response.status_code == 403:
            logger.warning(f"403 Forbidden: {request.path} - Possível erro CSRF")
        
        return response
    
    def _log_post_details(self, request):
        """Log detalhado de POST request para debug CSRF."""
        referer = request.META.get('HTTP_REFERER', 'N/A')
        origin = request.META.get('HTTP_ORIGIN', 'N/A')
        host = request.get_host()
        user_agent = request.META.get('HTTP_USER_AGENT', 'N/A')[:80]
        
        # CSRF específico
        csrf_cookie = request.COOKIES.get('csrftoken')
        csrf_post = request.POST.get('csrfmiddlewaretoken', 'N/A')
        csrf_header = request.META.get('HTTP_X_CSRFTOKEN', 'N/A')
        
        logger.debug(f"POST {request.path}")
        logger.debug(f"  Host: {host}")
        logger.debug(f"  Referer: {referer}")
        logger.debug(f"  Origin: {origin}")
        logger.debug(f"  User-Agent: {user_agent}")
        logger.debug(f"  CSRF Cookie existe: {bool(csrf_cookie)}")
        logger.debug(f"  CSRF POST token existe: {csrf_post != 'N/A'}")
        logger.debug(f"  CSRF Header existe: {csrf_header != 'N/A'}")
        logger.debug(f"  X-Forwarded-Proto: {request.META.get('HTTP_X_FORWARDED_PROTO', 'N/A')}")
        logger.debug(f"  Secure (HTTPS): {request.is_secure()}")


class CongelamentoMiddleware:
    """
    Bloqueia o acesso ao portal de alunos cujas matrículas estão congeladas.
    Redireciona para a página de confirmação de matrícula.
    """

    # URLs que alunos congelados ainda podem aceder
    URLS_PERMITIDAS = [
        '/confirmacao-matricula/',
        '/confirmacao-estado/',
        '/acesso-congelado/',
        '/accounts/login/',
        '/accounts/logout/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and hasattr(request.user, 'is_aluno')
            and request.user.is_aluno
        ):
            # Verifica se o path actual é permitido a alunos congelados
            path = request.path
            permitida = any(path.startswith(url) for url in self.URLS_PERMITIDAS)

            if not permitida:
                try:
                    from academico.models import Aluno
                    aluno = Aluno.objects.get(usuario=request.user)
                    if aluno.esta_congelado:
                        from django.shortcuts import redirect
                        return redirect('acesso_congelado')
                except Aluno.DoesNotExist:
                    pass

        return self.get_response(request)