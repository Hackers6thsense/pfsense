<?php
/**
 * Configuration Manager
 */

namespace PfSenseAI\Utils;

class Config
{
    private static $instance;
    private $config = [];

    public function __construct()
    {
        $this->loadConfig();
    }

    public static function getInstance()
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function loadConfig()
    {
        $this->config = [
            'pfsense' => [
                'host' => $_ENV['PFSENSE_HOST'] ?? '192.168.1.1',
                'username' => $_ENV['PFSENSE_USERNAME'] ?? 'admin',
                'password' => $_ENV['PFSENSE_PASSWORD'] ?? '',
                'api_key' => $_ENV['PFSENSE_API_KEY'] ?? '',
                'timeout' => 30,
                'verify_ssl' => false, // pfSense often uses self-signed certs
            ],
            'ai' => [
                'providers' => [
                    'mistral' => [
                        'api_key' => $_ENV['MISTRAL_API_KEY'] ?? '',
                        'model' => $_ENV['MISTRAL_MODEL'] ?? 'mistral-large',
                        'base_url' => 'https://api.mistral.ai/v1',
                    ],
                    'groq' => [
                        'api_key' => $_ENV['GROQ_API_KEY'] ?? '',
                        'model' => $_ENV['GROQ_MODEL'] ?? 'mixtral-8x7b-32768',
                        'base_url' => 'https://api.groq.com/openai/v1',
                    ],
                    'gemini' => [
                        'api_key' => $_ENV['GEMINI_API_KEY'] ?? '',
                        'model' => $_ENV['GEMINI_MODEL'] ?? 'gemini-pro',
                        'base_url' => 'https://generativelanguage.googleapis.com',
                    ],
                ],
                'primary_provider' => $_ENV['PRIMARY_AI_PROVIDER'] ?? 'mistral',
                'fallback_providers' => explode(',', $_ENV['FALLBACK_AI_PROVIDERS'] ?? 'groq,gemini'),
                'timeout' => (int)($_ENV['REQUEST_TIMEOUT'] ?? 30),
                'max_retries' => (int)($_ENV['MAX_RETRIES'] ?? 3),
            ],
            'app' => [
                'env' => $_ENV['APP_ENV'] ?? 'production',
                'debug' => $_ENV['APP_DEBUG'] ?? false,
                'timezone' => $_ENV['APP_TIMEZONE'] ?? 'UTC',
                'log_level' => $_ENV['APP_LOG_LEVEL'] ?? 'info',
            ],
            'session' => [
                'timeout' => (int)($_ENV['SESSION_TIMEOUT'] ?? 3600),
            ],
        ];
    }

    public function get($path, $default = null)
    {
        $keys = explode('.', $path);
        $value = $this->config;

        foreach ($keys as $key) {
            if (!isset($value[$key])) {
                return $default;
            }
            $value = $value[$key];
        }

        return $value;
    }

    public function set($path, $value)
    {
        $keys = explode('.', $path);
        $config = &$this->config;

        foreach ($keys as $key) {
            if (!isset($config[$key])) {
                $config[$key] = [];
            }
            $config = &$config[$key];
        }

        $config = $value;
    }
}
