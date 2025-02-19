from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from oauth.utils import jwt_login_required
from .models import ChatMessage
import logging

logger = logging.getLogger(__name__)

# Create your views here.
@csrf_exempt
@jwt_login_required
def chat_view(request: HttpRequest) -> HttpResponse:
    try:
        logger.info("Chat view called")
        # Obtener el canal de la solicitud (por defecto "general")
        current_channel = request.POST.get('channel', 'general')  # Usar POST para cambiar el canal

        if request.method == 'POST':
            # Guardar nuevo mensaje
            message_content = request.POST.get('message')
            if not message_content:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # Crear y guardar el mensaje
            new_message = ChatMessage.objects.create(
                sender=request.user,
                message=message_content,
                channel=current_channel
            )
            logger.info(f"New message in {current_channel} from {new_message.sender.username}: {new_message.content}")
        
            # Formatear el mensaje para devolverlo al frontend
            return HttpResponse(f"<p><strong>{new_message.sender.username}:</strong> {new_message.content}</p>")
    
        # Recuperar mensajes del canal actual
        messages = ChatMessage.objects.filter(channel=current_channel).order_by('timestamp')
        context = {
            'user': request.user,
            'messages': messages,
            'current_channel': current_channel,
            'channels': ['general', 'torneos', 'offtopic'],  # Canales fijos
        }
        return render(request, 'chat.html', context)
    except Exception as e:
        logger.error(f"Error in chat_view: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)