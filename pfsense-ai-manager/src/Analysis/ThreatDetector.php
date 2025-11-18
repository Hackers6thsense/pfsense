<?php
/**
 * Security Threat Detector
 */

namespace PfSenseAI\Analysis;

use PfSenseAI\AI\AIFactory;
use PfSenseAI\PfSense\PfSenseClient;
use PfSenseAI\Utils\Logger;

class ThreatDetector
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
     * Detect security threats
     */
    public function detectThreats(): array
    {
        try {
            $logs = $this->pfSenseClient->getLogs('', 500);
            $threats = $this->identifyThreats($logs);
            
            $report = [
                'threats_found' => count($threats),
                'critical' => 0,
                'high' => 0,
                'medium' => 0,
                'low' => 0,
                'threats' => [],
            ];

            foreach ($threats as $threat) {
                $severity = $threat['severity'] ?? 'low';
                $report[strtolower($severity)]++;
                $report['threats'][] = $threat;
            }

            // Get AI analysis
            if (!empty($threats)) {
                $aiAnalysis = $this->getAIThreatAnalysis($threats);
                $report['ai_recommendation'] = $aiAnalysis;
            }

            return [
                'status' => 'success',
                'report' => $report,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Threat detection failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Analyze specific threat
     */
    public function analyzeThreat(array $threatData): array
    {
        try {
            $prompt = "Analyze this security threat from pfSense: " . json_encode($threatData);
            $analysis = $this->aiFactory->analyze(json_encode($threatData), 'threat');
            
            return [
                'status' => 'success',
                'threat' => $threatData,
                'analysis' => $analysis,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Threat analysis failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get threat dashboard
     */
    public function getDashboard(): array
    {
        try {
            $threats = $this->detectThreats();
            $arpTable = $this->pfSenseClient->getARPTable();
            
            return [
                'status' => 'success',
                'threats' => $threats,
                'connected_devices' => count($arpTable),
                'services' => $this->pfSenseClient->getServices(),
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Dashboard generation failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    private function identifyThreats(array $logs): array
    {
        $threats = [];
        $threatPatterns = [
            'failed_login' => ['pattern' => 'failed', 'severity' => 'medium'],
            'port_scan' => ['pattern' => 'port.*scan', 'severity' => 'high'],
            'ddos' => ['pattern' => 'ddos|flood', 'severity' => 'critical'],
            'unauthorized_access' => ['pattern' => 'denied|unauthorized', 'severity' => 'high'],
        ];

        foreach ($logs as $log) {
            $logText = $log['msg'] ?? '';
            
            foreach ($threatPatterns as $type => $pattern) {
                if (preg_match('/' . $pattern['pattern'] . '/i', $logText)) {
                    $threats[] = [
                        'type' => $type,
                        'severity' => $pattern['severity'],
                        'message' => $logText,
                        'timestamp' => $log['time'] ?? date('Y-m-d H:i:s'),
                    ];
                    break;
                }
            }
        }

        return array_slice($threats, 0, 50); // Limit to 50 threats
    }

    private function getAIThreatAnalysis(array $threats): string
    {
        $threatSummary = array_map(function($t) {
            return $t['type'] . ' (' . $t['severity'] . ')';
        }, array_slice($threats, 0, 10));

        $prompt = "Based on these detected threats: " . implode(', ', $threatSummary) . 
                  ". Provide security recommendations and actions to take.";
        
        return $this->aiFactory->chat($prompt, ['role' => 'security_analyst']);
    }
}
