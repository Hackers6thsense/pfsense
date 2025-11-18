<?php
/**
 * Configuration Analyzer
 */

namespace PfSenseAI\Analysis;

use PfSenseAI\AI\AIFactory;
use PfSenseAI\PfSense\PfSenseClient;
use PfSenseAI\Utils\Logger;

class ConfigAnalyzer
{
    private $aiFactory;
    private $pfSenseClient;
    private $logger;

    public function __construct()
    {
        $this->aiFactory = AIFactory::getInstance();
        $this->pfSenseClient = new PfSenseClient();
        $this->logger = Logger::getInstance();
    }

    /**
     * Analyze current configuration
     */
    public function analyze(): array
    {
        try {
            $rules = $this->pfSenseClient->getRules();
            $status = $this->pfSenseClient->getStatus();
            
            $analysis = $this->analyzeRules($rules);
            
            // Get AI recommendations
            $aiRecommendations = $this->getAIRecommendations($rules, $status);
            
            return [
                'status' => 'success',
                'total_rules' => count($rules),
                'analysis' => $analysis,
                'ai_recommendations' => $aiRecommendations,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Configuration analysis failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get recommendations
     */
    public function getRecommendations(string $type = 'security'): array
    {
        try {
            $status = $this->pfSenseClient->getStatus();
            $rules = $this->pfSenseClient->getRules();
            
            $recommendations = [];

            if ($type === 'security' || $type === 'all') {
                $recommendations = array_merge($recommendations, $this->securityRecommendations($rules));
            }

            if ($type === 'performance' || $type === 'all') {
                $recommendations = array_merge($recommendations, $this->performanceRecommendations($status));
            }

            // Get AI-enhanced recommendations
            $prompt = "Based on pfSense configuration with " . count($rules) . " rules, provide " . $type . " recommendations.";
            $aiRecommendation = $this->aiFactory->chat($prompt, ['role' => 'firewall_admin']);

            return [
                'status' => 'success',
                'type' => $type,
                'recommendations' => $recommendations,
                'ai_insights' => $aiRecommendation,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Recommendations failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    private function analyzeRules(array $rules): array
    {
        $analysis = [
            'total_rules' => count($rules),
            'enabled_rules' => 0,
            'disabled_rules' => 0,
            'pass_rules' => 0,
            'block_rules' => 0,
            'issues' => [],
        ];

        foreach ($rules as $rule) {
            if ($rule['enabled'] ?? false) {
                $analysis['enabled_rules']++;
            } else {
                $analysis['disabled_rules']++;
            }

            if (($rule['type'] ?? '') === 'pass') {
                $analysis['pass_rules']++;
            } elseif (($rule['type'] ?? '') === 'block') {
                $analysis['block_rules']++;
            }
        }

        // Check for potential issues
        if ($analysis['enabled_rules'] > 100) {
            $analysis['issues'][] = [
                'severity' => 'warning',
                'message' => 'Large number of enabled rules may impact performance',
            ];
        }

        return $analysis;
    }

    private function securityRecommendations(array $rules): array
    {
        $recommendations = [];

        // Check if HTTPS is enforced
        $httpsFound = false;
        foreach ($rules as $rule) {
            if (strpos($rule['destination']['port'] ?? '', '443') !== false) {
                $httpsFound = true;
                break;
            }
        }

        if (!$httpsFound) {
            $recommendations[] = [
                'priority' => 'high',
                'recommendation' => 'Consider adding rules to enforce HTTPS traffic',
            ];
        }

        // Check for overly permissive rules
        foreach ($rules as $rule) {
            if (($rule['source'] ?? '') === 'any' && ($rule['destination'] ?? '') === 'any') {
                $recommendations[] = [
                    'priority' => 'high',
                    'recommendation' => 'Review rules with "any" source/destination for security',
                ];
                break;
            }
        }

        return $recommendations;
    }

    private function performanceRecommendations(array $status): array
    {
        return [
            [
                'priority' => 'medium',
                'recommendation' => 'Monitor system load and consider rule optimization',
            ],
        ];
    }

    private function getAIRecommendations(array $rules, array $status): string
    {
        $config = [
            'total_rules' => count($rules),
            'system_uptime' => $status['uptime'] ?? 'unknown',
        ];

        $prompt = "Review this pfSense configuration and provide optimization recommendations: " . 
                  json_encode($config);
        
        return $this->aiFactory->chat($prompt, ['role' => 'firewall_admin']);
    }
}
