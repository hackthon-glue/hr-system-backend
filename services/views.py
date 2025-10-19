"""
API Views for HR Agent services
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .hr_agent_services import chat_with_concierge

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Add authentication later
def concierge_chat(request):
    """
    Chat with candidate concierge

    Request body:
    {
        "query": "Query content",
        "context": {
            "candidate_info": {...}
        }
    }
    """
    try:
        query = request.data.get('query')
        context = request.data.get('context', {})

        if not query:
            return Response(
                {'error': 'query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Concierge chat request: {query[:100]}")

        # Call concierge agent
        result = chat_with_concierge(
            user_query=query,
            candidate_info=context.get('candidate_info')
        )

        return Response({
            'status': 'success',
            'agent': 'concierge',
            'result': result
        })

    except Exception as e:
        logger.error(f"Error in concierge chat: {e}", exc_info=True)
        return Response(
            {
                'status': 'error',
                'error': str(e),
                'message': 'An error occurred while chatting with the concierge. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
