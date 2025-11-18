<?php
/**
 * AI Provider Factory with Fallback Support
 */

namespace PfSenseAI\AI;

use PfSenseAI\Utils\Logger;
use PfSenseAI\Utils\Config;

class AIFactory
{
    private static $instance;
    private $providers = [];
    private $currentProvider;
    private $logger;
    private $config;

    public function __construct()
    {
        $this->logger = Logger::getInstance();
        $this->config = Config::getInstance();
        $this->initializeProviders();
    }

    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function initializeProviders()
    {
        $this->providers = [
            'mistral' => new MistralProvider(),
            'groq' => new GroqProvider(),
            'gemini' => new GeminiProvider(),
        ];
    }

    /**
     * Get the appropriate AI provider with fallback support
     */
    public function getProvider(): AIProvider
    {
        $primaryProvider = $this->config->get('ai.primary_provider', 'mistral');
        $fallbackProviders = $this->config->get('ai.fallback_providers', ['groq', 'gemini']);

        // Try primary provider first
        if ($this->providers[$primaryProvider]->isAvailable()) {
            $this->currentProvider = $primaryProvider;
            return $this->providers[$primaryProvider];
        }

        $this->logger->warning('Primary provider {provider} not available, trying fallbacks', 
            ['provider' => $primaryProvider]);

        // Try fallback providers
        foreach ($fallbackProviders as $provider) {
            if (isset($this->providers[$provider]) && $this->providers[$provider]->isAvailable()) {
                $this->logger->info('Using fallback provider: {provider}', ['provider' => $provider]);
                $this->currentProvider = $provider;
                return $this->providers[$provider];
            }
        }

        throw new \Exception('No AI providers available. Please configure at least one API key.');
    }

    /**
     * Get a specific provider
     */
    public function getProviderByName(string $name): AIProvider
    {
        if (!isset($this->providers[$name])) {
            throw new \Exception("Provider '$name' not found");
        }

        if (!$this->providers[$name]->isAvailable()) {
            throw new \Exception("Provider '$name' is not configured");
        }

        return $this->providers[$name];
    }

    /**
     * Get current provider name
     */
    public function getCurrentProviderName(): string
    {
        return $this->currentProvider ?? $this->config->get('ai.primary_provider', 'mistral');
    }

    /**
     * Get all available providers
     */
    public function getAvailableProviders(): array
    {
        $available = [];
        foreach ($this->providers as $name => $provider) {
            if ($provider->isAvailable()) {
                $available[$name] = $provider->getModelInfo();
            }
        }
        return $available;
    }

    /**
     * Chat with automatic fallback
     */
    public function chat(string $message, array $context = []): string
    {
        $maxRetries = $this->config->get('ai.max_retries', 3);
        $attempts = 0;

        while ($attempts < $maxRetries) {
            try {
                $provider = $this->getProvider();
                return $provider->chat($message, $context);
            } catch (\Exception $e) {
                $attempts++;
                $this->logger->warning('AI provider failed (attempt {attempt}): {error}', 
                    ['attempt' => $attempts, 'error' => $e->getMessage()]);

                if ($attempts >= $maxRetries) {
                    throw new \Exception('All AI providers failed after ' . $maxRetries . ' attempts');
                }
            }
        }
    }

    /**
     * Analyze with automatic fallback
     */
    public function analyze(string $content, string $type = 'general'): array
    {
        try {
            $provider = $this->getProvider();
            return $provider->analyze($content, $type);
        } catch (\Exception $e) {
            $this->logger->error('Analysis failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }
}
