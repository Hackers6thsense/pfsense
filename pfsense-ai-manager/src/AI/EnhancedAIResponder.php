<?php
/**
 * Enhanced AI Responder with reasoning, caveats, and follow-up questions
 */

namespace PfSenseAI\AI;

use PfSenseAI\Utils\Logger;

class EnhancedAIResponder
{
    private $aiFactory;
    private $logger;

    public function __construct()
    {
        $this->aiFactory = AIFactory::getInstance();
        $this->logger = Logger::getInstance();
    }

    /**
     * Get enhanced response with reasoning, confidence, caveats, and follow-ups
     */
    public function getEnhancedResponse(
        string $message,
        array $context = [],
        array $firewall_context = []
    ): array {
        try {
            // Get base response
            $baseResponse = $this->aiFactory->chat($message, $context);

            // Enhance with reasoning and analysis
            $enhanced = [
                'response' => $baseResponse,
                'reasoning' => $this->getReasoningProcess($message, $baseResponse),
                'confidence' => $this->calculateConfidence($message, $baseResponse),
                'caveats' => $this->generateCaveats($message, $baseResponse),
                'follow_up_questions' => $this->generateFollowUpQuestions($message, $baseResponse),
                'metadata' => [
                    'provider' => $this->aiFactory->getCurrentProviderName(),
                    'model' => $this->getModelInfo(),
                    'timestamp' => date('Y-m-d H:i:s'),
                    'firewall_context_used' => !empty($firewall_context),
                ],
            ];

            return $enhanced;
        } catch (\Exception $e) {
            $this->logger->error('Enhanced response failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Stream response with real-time output
     */
    public function streamResponse(
        string $message,
        array $context = [],
        callable $onChunk = null
    ): void {
        try {
            // Set appropriate headers for streaming
            header('Content-Type: text/event-stream');
            header('Cache-Control: no-cache');
            header('Connection: keep-alive');

            // Send initial message
            $this->sendSSEEvent('start', ['message' => 'Processing your request...']);
            flush();

            // Get response (in real scenario, this would be streaming from AI provider)
            $response = $this->aiFactory->chat($message, $context);

            // Stream response in chunks
            $chunks = str_split($response, 50); // 50 char chunks
            foreach ($chunks as $chunk) {
                $this->sendSSEEvent('chunk', ['text' => $chunk]);
                if ($onChunk) {
                    $onChunk($chunk);
                }
                flush();
                usleep(50000); // 50ms delay for natural streaming effect
            }

            // Send analysis after response
            $reasoning = $this->getReasoningProcess($message, $response);
            $this->sendSSEEvent('reasoning', ['process' => $reasoning]);
            flush();

            // Send caveats
            $caveats = $this->generateCaveats($message, $response);
            $this->sendSSEEvent('caveats', ['warnings' => $caveats]);
            flush();

            // Send follow-up questions
            $followUps = $this->generateFollowUpQuestions($message, $response);
            $this->sendSSEEvent('follow_ups', ['questions' => $followUps]);
            flush();

            // Send completion
            $this->sendSSEEvent('complete', ['status' => 'done']);
            flush();
        } catch (\Exception $e) {
            $this->logger->error('Streaming failed: {error}', ['error' => $e->getMessage()]);
            $this->sendSSEEvent('error', ['message' => $e->getMessage()]);
        }
    }

    /**
     * Get multi-turn conversation with full context
     */
    public function getMultiTurnResponse(
        array $messages,
        array $firewall_context = []
    ): array {
        try {
            $responses = [];

            foreach ($messages as $index => $msg) {
                $previousContext = array_slice($responses, -5); // Last 5 responses for context
                
                $response = $this->getEnhancedResponse(
                    $msg,
                    ['previous_context' => $previousContext],
                    $firewall_context
                );

                $responses[] = $response;

                // Add slight delay between requests
                if ($index < count($messages) - 1) {
                    usleep(500000); // 0.5s delay
                }
            }

            return [
                'status' => 'success',
                'messages_processed' => count($messages),
                'responses' => $responses,
                'conversation_summary' => $this->summarizeConversation($messages, $responses),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Multi-turn conversation failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Generate reasoning process explanation
     */
    private function getReasoningProcess(string $question, string $response): array
    {
        // Prompt AI to explain its reasoning
        $reasoningPrompt = "Explain your reasoning for the previous response in 2-3 steps. Be concise.";
        
        try {
            $reasoning = $this->aiFactory->chat($reasoningPrompt);
            return [
                'question_analyzed' => $this->extractKeywords($question),
                'reasoning_steps' => $this->parseReasoningSteps($reasoning),
                'logic_used' => $this->identifyLogicType($question),
            ];
        } catch (\Exception $e) {
            return [
                'error' => 'Could not generate reasoning',
                'question_analyzed' => $this->extractKeywords($question),
            ];
        }
    }

    /**
     * Calculate confidence score for response
     */
    private function calculateConfidence(string $question, string $response): array
    {
        $factors = [
            'question_clarity' => $this->scoreQuestionClarity($question),
            'response_completeness' => $this->scoreResponseCompleteness($response),
            'terminology_accuracy' => $this->scoreTerminologyAccuracy($response),
        ];

        $average = array_sum($factors) / count($factors);

        return [
            'overall' => round($average, 2),
            'level' => $this->getConfidenceLevel($average),
            'factors' => $factors,
        ];
    }

    /**
     * Generate caveats and warnings
     */
    private function generateCaveats(string $question, string $response): array
    {
        $caveats = [];

        // Check for potentially dangerous operations
        if (preg_match('/delete|remove|disable|block all/i', $response)) {
            $caveats[] = [
                'severity' => 'high',
                'warning' => 'This recommendation involves potentially destructive actions. Test in a safe environment first.',
            ];
        }

        // Check for security-related caveats
        if (preg_match('/security|threat|attack|vulnerable/i', $response)) {
            $caveats[] = [
                'severity' => 'medium',
                'warning' => 'Security recommendations should be validated against your specific environment and requirements.',
            ];
        }

        // Check for limitation caveats
        if (preg_match('/might|may|could|possibly|depending on/i', $response)) {
            $caveats[] = [
                'severity' => 'low',
                'warning' => 'This response contains conditional guidance. Verify applicability to your situation.',
            ];
        }

        // Add default caveat
        if (empty($caveats)) {
            $caveats[] = [
                'severity' => 'info',
                'warning' => 'Always test changes in a non-production environment first.',
            ];
        }

        return $caveats;
    }

    /**
     * Generate follow-up questions
     */
    private function generateFollowUpQuestions(string $question, string $response): array
    {
        $followUps = [];

        // Suggest clarifying questions based on response
        if (preg_match('/traffic|bandwidth/i', $question)) {
            $followUps[] = 'Would you like to set up traffic alerts for specific thresholds?';
        }

        if (preg_match('/threat|attack/i', $question)) {
            $followUps[] = 'Should we review and strengthen your current firewall rules?';
        }

        if (preg_match('/rule|config/i', $question)) {
            $followUps[] = 'Do you need help implementing these configuration changes?';
        }

        if (preg_match('/log|pattern/i', $question)) {
            $followUps[] = 'Would you like to set up automated monitoring for this pattern?';
        }

        // Always suggest exploring related topics
        $followUps[] = 'Would you like recommendations for related security improvements?';

        return array_slice($followUps, 0, 3); // Return top 3 follow-ups
    }

    /**
     * Summarize conversation
     */
    private function summarizeConversation(array $questions, array $responses): array
    {
        $topics = [];
        $sentiment = 'neutral';

        foreach ($questions as $q) {
            $keywords = $this->extractKeywords($q);
            $topics = array_merge($topics, $keywords);
        }

        return [
            'total_messages' => count($questions),
            'topics_discussed' => array_unique($topics),
            'conversation_type' => $this->identifyConversationType($questions),
            'sentiment' => $sentiment,
        ];
    }

    /**
     * Send Server-Sent Event
     */
    private function sendSSEEvent(string $event, array $data): void
    {
        echo "event: {$event}\n";
        echo "data: " . json_encode($data) . "\n\n";
    }

    /**
     * Extract keywords from text
     */
    private function extractKeywords(string $text): array
    {
        $keywords = [];
        $patterns = [
            'firewall' => 'firewall|pfsense|fw',
            'threat' => 'threat|attack|threat|malicious',
            'traffic' => 'traffic|bandwidth|flow|packet',
            'log' => 'log|logs|event|audit',
            'rule' => 'rule|rules|policy|filter',
            'performance' => 'performance|speed|latency|optimize',
            'security' => 'security|secure|encryption|ssl',
        ];

        foreach ($patterns as $category => $pattern) {
            if (preg_match('/' . $pattern . '/i', $text)) {
                $keywords[] = $category;
            }
        }

        return $keywords;
    }

    /**
     * Parse reasoning steps from text
     */
    private function parseReasoningSteps(string $reasoning): array
    {
        $steps = [];
        // Split by common delimiters
        $lines = preg_split('/[\r\n]+/', $reasoning);
        
        foreach (array_slice($lines, 0, 5) as $line) {
            $line = trim($line);
            if (!empty($line) && strlen($line) > 10) {
                $steps[] = preg_replace('/^[\d\.\-\*\s]+/', '', $line);
            }
        }

        return array_slice($steps, 0, 3);
    }

    /**
     * Identify type of logic used
     */
    private function identifyLogicType(string $question): string
    {
        if (preg_match('/what|who|when|where/i', $question)) {
            return 'analytical';
        } elseif (preg_match('/how|why|what if/i', $question)) {
            return 'explanatory';
        } elseif (preg_match('/should|recommend|suggest/i', $question)) {
            return 'advisory';
        } elseif (preg_match('/help|fix|solve|resolve/i', $question)) {
            return 'troubleshooting';
        }
        return 'general';
    }

    /**
     * Score question clarity
     */
    private function scoreQuestionClarity(string $question): float
    {
        $score = 0.5;
        
        if (strlen($question) > 20) $score += 0.1;
        if (strlen($question) > 50) $score += 0.15;
        if (preg_match('/\?/', $question)) $score += 0.15;
        if (preg_match('/specific|particular|exactly/i', $question)) $score += 0.1;

        return min($score, 1.0);
    }

    /**
     * Score response completeness
     */
    private function scoreResponseCompleteness(string $response): float
    {
        $score = 0.5;
        
        if (strlen($response) > 100) $score += 0.15;
        if (strlen($response) > 300) $score += 0.15;
        if (substr_count($response, '.') > 3) $score += 0.1;
        if (preg_match('/therefore|thus|consequently|result/i', $response)) $score += 0.1;

        return min($score, 1.0);
    }

    /**
     * Score terminology accuracy
     */
    private function scoreTerminologyAccuracy(string $response): float
    {
        $score = 0.5;
        $technicalTerms = ['firewall', 'packet', 'protocol', 'encryption', 'authentication', 'rules', 'traffic'];
        
        foreach ($technicalTerms as $term) {
            if (stripos($response, $term) !== false) {
                $score += 0.05;
            }
        }

        return min($score, 1.0);
    }

    /**
     * Get confidence level description
     */
    private function getConfidenceLevel(float $score): string
    {
        if ($score >= 0.9) return 'very_high';
        if ($score >= 0.75) return 'high';
        if ($score >= 0.6) return 'medium';
        if ($score >= 0.45) return 'low';
        return 'very_low';
    }

    /**
     * Identify conversation type
     */
    private function identifyConversationType(array $questions): string
    {
        $text = implode(' ', $questions);
        
        if (preg_match('/threat|attack|security/i', $text)) return 'security_focused';
        if (preg_match('/performance|optimize|slow/i', $text)) return 'optimization';
        if (preg_match('/help|fix|broken|error/i', $text)) return 'troubleshooting';
        if (preg_match('/how|explain|understand/i', $text)) return 'educational';
        
        return 'general';
    }

    /**
     * Get model information
     */
    private function getModelInfo(): string
    {
        $provider = $this->aiFactory->getCurrentProviderName();
        return "{$provider}_ai";
    }
}
