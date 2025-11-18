<?php
/**
 * Conversation Manager - Handles conversation history and context
 */

namespace PfSenseAI\AI;

use PfSenseAI\Utils\Cache;
use PfSenseAI\Utils\Logger;

class ConversationManager
{
    private $cache;
    private $logger;
    private $conversationId;
    private $maxMessages = 50;
    private $contextWindow = 10; // Keep last 10 messages for context

    public function __construct(string $conversationId = null)
    {
        $this->cache = Cache::getInstance();
        $this->logger = Logger::getInstance();
        $this->conversationId = $conversationId ?? $this->generateConversationId();
    }

    /**
     * Add message to conversation history
     */
    public function addMessage(string $role, string $content, array $metadata = []): array
    {
        $message = [
            'role' => $role, // 'user', 'assistant', 'system'
            'content' => $content,
            'timestamp' => date('Y-m-d H:i:s'),
            'metadata' => $metadata,
        ];

        $history = $this->getFullHistory();
        $history[] = $message;

        // Keep only recent messages
        if (count($history) > $this->maxMessages) {
            $history = array_slice($history, -$this->maxMessages);
        }

        $this->saveHistory($history);
        $this->logger->debug('Message added to conversation {id}', ['id' => $this->conversationId]);

        return $message;
    }

    /**
     * Get conversation history
     */
    public function getHistory(int $limit = null): array
    {
        $history = $this->getFullHistory();
        return $limit ? array_slice($history, -$limit) : $history;
    }

    /**
     * Get context for AI (last N messages)
     */
    public function getContext(): array
    {
        $history = $this->getHistory($this->contextWindow);
        return array_map(function($msg) {
            return [
                'role' => $msg['role'],
                'content' => $msg['content'],
            ];
        }, $history);
    }

    /**
     * Get conversation summary
     */
    public function getSummary(): array
    {
        $history = $this->getFullHistory();
        $userMessages = array_filter($history, fn($m) => $m['role'] === 'user');
        $assistantMessages = array_filter($history, fn($m) => $m['role'] === 'assistant');

        return [
            'conversation_id' => $this->conversationId,
            'total_messages' => count($history),
            'user_messages' => count($userMessages),
            'assistant_messages' => count($assistantMessages),
            'started_at' => $history[0]['timestamp'] ?? null,
            'last_message_at' => end($history)['timestamp'] ?? null,
            'topics' => $this->extractTopics($userMessages),
        ];
    }

    /**
     * Clear conversation history
     */
    public function clear(): void
    {
        $this->cache->forget($this->getCacheKey());
        $this->logger->info('Conversation {id} cleared', ['id' => $this->conversationId]);
    }

    /**
     * Get conversation ID
     */
    public function getConversationId(): string
    {
        return $this->conversationId;
    }

    /**
     * Export conversation as markdown
     */
    public function exportAsMarkdown(): string
    {
        $history = $this->getFullHistory();
        $markdown = "# Conversation " . $this->conversationId . "\n\n";

        foreach ($history as $message) {
            $role = ucfirst($message['role']);
            $markdown .= "## " . $role . " (" . $message['timestamp'] . ")\n";
            $markdown .= $message['content'] . "\n\n";
        }

        return $markdown;
    }

    private function getFullHistory(): array
    {
        return $this->cache->get($this->getCacheKey(), []) ?? [];
    }

    private function saveHistory(array $history): void
    {
        // Cache for 24 hours
        $this->cache->set($this->getCacheKey(), $history, 86400);
    }

    private function getCacheKey(): string
    {
        return 'conversation_' . $this->conversationId;
    }

    private function generateConversationId(): string
    {
        return 'conv_' . bin2hex(random_bytes(8)) . '_' . time();
    }

    private function extractTopics(array $userMessages): array
    {
        $topics = [];
        $keywords = ['firewall', 'threat', 'traffic', 'log', 'rule', 'attack', 'security', 'performance'];

        foreach ($userMessages as $msg) {
            $content = strtolower($msg['content']);
            foreach ($keywords as $keyword) {
                if (strpos($content, $keyword) !== false && !in_array($keyword, $topics)) {
                    $topics[] = $keyword;
                }
            }
        }

        return array_slice($topics, 0, 5);
    }
}
