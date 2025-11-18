<?php
/**
 * Groq AI Provider
 */

namespace PfSenseAI\AI;

use GuzzleHttp\Client;
use PfSenseAI\Utils\Logger;
use PfSenseAI\Utils\Config;

class GroqProvider implements AIProvider
{
    private $client;
    private $apiKey;
    private $model;
    private $logger;
    private $config;

    public function __construct()
    {
        $this->config = Config::getInstance();
        $this->logger = Logger::getInstance();
        
        $groqConfig = $this->config->get('ai.providers.groq');
        $this->apiKey = $groqConfig['api_key'] ?? '';
        $this->model = $groqConfig['model'] ?? 'mixtral-8x7b-32768';

        $this->client = new Client([
            'base_uri' => $groqConfig['base_url'] ?? 'https://api.groq.com/openai/v1',
            'timeout' => $this->config->get('ai.timeout', 30),
        ]);
    }

    public function chat(string $message, array $context = []): string
    {
        if (!$this->isAvailable()) {
            throw new \Exception('Groq provider is not available');
        }

        try {
            $messages = [
                ['role' => 'system', 'content' => $this->buildSystemPrompt($context)],
                ['role' => 'user', 'content' => $message],
            ];

            $response = $this->client->post('chat/completions', [
                'headers' => [
                    'Authorization' => 'Bearer ' . $this->apiKey,
                    'Content-Type' => 'application/json',
                ],
                'json' => [
                    'model' => $this->model,
                    'messages' => $messages,
                    'temperature' => 0.7,
                    'max_tokens' => 2000,
                ],
            ]);

            $body = json_decode($response->getBody(), true);
            return $body['choices'][0]['message']['content'] ?? '';
        } catch (\Exception $e) {
            $this->logger->error('Groq API error: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function analyze(string $content, string $type = 'general'): array
    {
        $prompt = $this->buildAnalysisPrompt($content, $type);
        $response = $this->chat($prompt);

        try {
            return json_decode($response, true) ?? ['analysis' => $response];
        } catch (\Exception $e) {
            return ['analysis' => $response];
        }
    }

    public function getModelInfo(): array
    {
        return [
            'provider' => 'groq',
            'model' => $this->model,
            'available' => $this->isAvailable(),
        ];
    }

    public function isAvailable(): bool
    {
        return !empty($this->apiKey);
    }

    private function buildSystemPrompt(array $context = []): string
    {
        $prompt = "You are an expert pfSense firewall administrator and network security specialist.";
        $prompt .= " Provide concise, actionable responses.";
        
        if (isset($context['role'])) {
            $prompt .= " Your role: " . $context['role'];
        }
        
        return $prompt;
    }

    private function buildAnalysisPrompt(string $content, string $type): string
    {
        $prompts = [
            'threat' => "Analyze the following security threat and provide detailed analysis: {content}",
            'traffic' => "Analyze the following network traffic patterns: {content}",
            'log' => "Analyze the following firewall logs and provide insights: {content}",
            'config' => "Review the following pfSense configuration and provide recommendations: {content}",
        ];

        $template = $prompts[$type] ?? $prompts['general'] ?? "Analyze the following: {content}";
        return str_replace('{content}', $content, $template);
    }
}
