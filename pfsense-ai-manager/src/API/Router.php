<?php
/**
 * API Router
 */

namespace PfSenseAI\API;

use PfSenseAI\Utils\Logger;

class Router
{
    private $logger;
    private $routes = [];

    public function __construct()
    {
        $this->logger = Logger::getInstance();
        $this->registerRoutes();
    }

    private function registerRoutes()
    {
        // Analysis routes
        $this->routes['POST /api/analysis/traffic'] = 'PfSenseAI\API\Endpoints\AnalysisEndpoint@analyzeTraffic';
        $this->routes['GET /api/analysis/traffic/history'] = 'PfSenseAI\API\Endpoints\AnalysisEndpoint@getTrafficHistory';
        $this->routes['GET /api/analysis/anomalies'] = 'PfSenseAI\API\Endpoints\AnalysisEndpoint@detectAnomalies';

        // Threat routes
        $this->routes['GET /api/threats'] = 'PfSenseAI\API\Endpoints\ThreatEndpoint@getThreats';
        $this->routes['POST /api/threats/analyze'] = 'PfSenseAI\API\Endpoints\ThreatEndpoint@analyzeThreat';
        $this->routes['GET /api/threats/dashboard'] = 'PfSenseAI\API\Endpoints\ThreatEndpoint@getDashboard';

        // Configuration routes
        $this->routes['GET /api/config/rules'] = 'PfSenseAI\API\Endpoints\ConfigEndpoint@getRules';
        $this->routes['POST /api/config/analyze'] = 'PfSenseAI\API\Endpoints\ConfigEndpoint@analyze';
        $this->routes['GET /api/recommendations'] = 'PfSenseAI\API\Endpoints\ConfigEndpoint@getRecommendations';

        // Log routes
        $this->routes['GET /api/logs'] = 'PfSenseAI\API\Endpoints\LogEndpoint@getLogs';
        $this->routes['POST /api/logs/analyze'] = 'PfSenseAI\API\Endpoints\LogEndpoint@analyze';
        $this->routes['POST /api/logs/search'] = 'PfSenseAI\API\Endpoints\LogEndpoint@search';
        $this->routes['GET /api/logs/patterns'] = 'PfSenseAI\API\Endpoints\LogEndpoint@getPatterns';

        // Chat routes (Enhanced)
        $this->routes['POST /api/chat'] = 'PfSenseAI\API\Endpoints\ChatEndpoint@send';
        $this->routes['POST /api/chat/multi-turn'] = 'PfSenseAI\API\Endpoints\ChatEndpoint@multiTurn';
        $this->routes['GET /api/chat/history'] = 'PfSenseAI\API\Endpoints\ChatEndpoint@getHistory';
        $this->routes['GET /api/chat/summary'] = 'PfSenseAI\API\Endpoints\ChatEndpoint@getSummary';
        $this->routes['POST /api/chat/clear'] = 'PfSenseAI\API\Endpoints\ChatEndpoint@clearHistory';

        // System routes
        $this->routes['GET /api/system/status'] = 'PfSenseAI\API\Endpoints\SystemEndpoint@status';
        $this->routes['GET /api/system/providers'] = 'PfSenseAI\API\Endpoints\SystemEndpoint@getProviders';
    }

    public function dispatch(string $method, string $path)
    {
        $route = "{$method} {$path}";

        if (isset($this->routes[$route])) {
            $this->handleRoute($this->routes[$route]);
        } else {
            $this->notFound();
        }
    }

    private function handleRoute(string $handler)
    {
        try {
            [$class, $method] = explode('@', $handler);
            
            if (!class_exists($class)) {
                throw new \Exception("Handler class not found: $class");
            }

            $instance = new $class();
            
            if (!method_exists($instance, $method)) {
                throw new \Exception("Handler method not found: $method");
            }

            $instance->$method();
        } catch (\Exception $e) {
            $this->logger->error('Route handler error: {error}', ['error' => $e->getMessage()]);
            http_response_code(500);
            echo json_encode([
                'error' => $e->getMessage(),
                'status' => 'error',
            ]);
        }
    }

    private function notFound()
    {
        http_response_code(404);
        echo json_encode([
            'error' => 'Endpoint not found',
            'status' => 'error',
        ]);
    }

    protected static function getInput(): array
    {
        $input = file_get_contents('php://input');
        return json_decode($input, true) ?? [];
    }

    protected static function response(array $data, int $statusCode = 200)
    {
        http_response_code($statusCode);
        echo json_encode($data);
    }
}
