<?php
/**
 * Chat Endpoint with Enhanced Features
 */

namespace PfSenseAI\API\Endpoints;

use PfSenseAI\AI\AIFactory;
use PfSenseAI\AI\ConversationManager;
use PfSenseAI\AI\EnhancedAIResponder;
use PfSenseAI\PfSense\DataCollector;
use PfSenseAI\API\Router;

class ChatEndpoint extends Router
{
    private $conversationManager;
    private $enhancedResponder;
    private $dataCollector;

    public function __construct()
    {
        $this->enhancedResponder = new EnhancedAIResponder();
        $this->dataCollector = new DataCollector();
    }

    /**
     * Send message with enhanced features
     */
    public function send()
    {
        try {
            $input = self::getInput();
            $message = $input['message'] ?? '';
            $conversationId = $input['conversation_id'] ?? null;
            $useStreaming = $input['streaming'] ?? false;
            $includeContext = $input['include_context'] ?? true;
            $enhancedResponse = $input['enhanced'] ?? true;

            if (empty($message)) {
                self::response(['error' => 'Message required'], 400);
                return;
            }

            // Initialize conversation manager
            $this->conversationManager = new ConversationManager($conversationId);

            // Get firewall context if requested
            $firewallContext = $includeContext ? $this->dataCollector->collectMetrics() : [];

            // Handle streaming
            if ($useStreaming) {
                $this->handleStreaming($message, $firewallContext);
                return;
            }

            // Get enhanced response
            if ($enhancedResponse) {
                $response = $this->enhancedResponder->getEnhancedResponse(
                    $message,
                    [],
                    $firewallContext
                );
            } else {
                $aiFactory = AIFactory::getInstance();
                $response = [
                    'response' => $aiFactory->chat($message),
                    'metadata' => [
                        'provider' => $aiFactory->getCurrentProviderName(),
                    ],
                ];
            }

            // Add to conversation history
            $this->conversationManager->addMessage('user', $message);
            $this->conversationManager->addMessage('assistant', $response['response'] ?? $response);

            self::response([
                'status' => 'success',
                'conversation_id' => $this->conversationManager->getConversationId(),
                'message' => $message,
                'response' => $response,
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Send multiple messages in conversation
     */
    public function multiTurn()
    {
        try {
            $input = self::getInput();
            $messages = $input['messages'] ?? [];
            $conversationId = $input['conversation_id'] ?? null;

            if (empty($messages)) {
                self::response(['error' => 'Messages array required'], 400);
                return;
            }

            $this->conversationManager = new ConversationManager($conversationId);

            // Get firewall context
            $firewallContext = $this->dataCollector->collectMetrics();

            // Process multiple messages
            $responses = $this->enhancedResponder->getMultiTurnResponse(
                $messages,
                $firewallContext
            );

            // Add all to history
            foreach ($messages as $msg) {
                $this->conversationManager->addMessage('user', $msg);
            }

            self::response([
                'status' => 'success',
                'conversation_id' => $this->conversationManager->getConversationId(),
                'multi_turn' => $responses,
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Get conversation history
     */
    public function getHistory()
    {
        try {
            $input = self::getInput();
            $conversationId = $input['conversation_id'] ?? $_GET['conversation_id'] ?? null;
            $limit = $input['limit'] ?? $_GET['limit'] ?? 50;

            if (!$conversationId) {
                self::response(['error' => 'Conversation ID required'], 400);
                return;
            }

            $this->conversationManager = new ConversationManager($conversationId);

            self::response([
                'status' => 'success',
                'conversation_id' => $conversationId,
                'history' => $this->conversationManager->getHistory($limit),
                'summary' => $this->conversationManager->getSummary(),
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Get conversation summary
     */
    public function getSummary()
    {
        try {
            $input = self::getInput();
            $conversationId = $input['conversation_id'] ?? $_GET['conversation_id'] ?? null;

            if (!$conversationId) {
                self::response(['error' => 'Conversation ID required'], 400);
                return;
            }

            $this->conversationManager = new ConversationManager($conversationId);

            self::response([
                'status' => 'success',
                'conversation_id' => $conversationId,
                'summary' => $this->conversationManager->getSummary(),
                'markdown_export' => $this->conversationManager->exportAsMarkdown(),
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Clear conversation history
     */
    public function clearHistory()
    {
        try {
            $input = self::getInput();
            $conversationId = $input['conversation_id'] ?? null;

            if (!$conversationId) {
                self::response(['error' => 'Conversation ID required'], 400);
                return;
            }

            $this->conversationManager = new ConversationManager($conversationId);
            $this->conversationManager->clear();

            self::response([
                'status' => 'success',
                'message' => 'Conversation cleared',
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Handle streaming response
     */
    private function handleStreaming(string $message, array $firewallContext): void
    {
        $this->enhancedResponder->streamResponse($message, [], function($chunk) {
            // Optional callback for each chunk
        });
    }
}
