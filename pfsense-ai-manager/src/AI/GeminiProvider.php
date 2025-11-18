<?php
/**
 * Google Gemini AI Provider
 */

namespace PfSenseAI\AI;

use GuzzleHttp\Client;
use PfSenseAI\Utils\Logger;
use PfSenseAI\Utils\Config;

class GeminiProvider implements AIProvider
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
        
        $geminiConfig = $this->config->get('ai.providers.gemini');
        $this->apiKey = $geminiConfig['api_key'] ?? '';
        $this->model = $geminiConfig['model'] ?? 'gemini-pro';

        $this->client = new Client([
            'base_uri' => $geminiConfig['base_url'] ?? 'https://generativelanguage.googleapis.com',
            'timeout' => $this->config->get('ai.timeout', 30),
        ]);
    }

    public function chat(string $message, array $context = []): string
    {
        if (!$this->isAvailable()) {
            throw new \Exception('Gemini provider is not available');
        }

        try {
            $systemPrompt = $this->buildSystemPrompt($context);
            $fullMessage = $systemPrompt . "\n\nUser: " . $message;

            $response = $this->client->post(
                "v1beta/models/{$this->model}:generateContent",
                [
                    'query' => ['key' => $this->apiKey],
                    'json' => [
                        'contents' => [
                            [
                                'parts' => [
                                    ['text' => $fullMessage],
                                ],
                            ],
                        ],
                        'generationConfig' => [
                            'temperature' => 0.7,
                            'maxOutputTokens' => 2000,
                        ],
                    ],
                ]
            );

            $body = json_decode($response->getBody(), true);
            return $body['candidates'][0]['content']['parts'][0]['text'] ?? '';
        } catch (\Exception $e) {
            $this->logger->error('Gemini API error: {error}', ['error' => $e->getMessage()]);
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
            'provider' => 'gemini',
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
