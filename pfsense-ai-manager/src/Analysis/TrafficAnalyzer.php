<?php
/**
 * Network Traffic Analyzer
 */

namespace PfSenseAI\Analysis;

use PfSenseAI\AI\AIFactory;
use PfSenseAI\PfSense\PfSenseClient;
use PfSenseAI\Utils\Logger;

class TrafficAnalyzer
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
     * Analyze network traffic
     */
    public function analyze(string $timeframe = 'last_hour'): array
    {
        try {
            $stats = $this->pfSenseClient->getTrafficStats();
            $interfaces = $this->pfSenseClient->getInterfaces();
            
            $summary = $this->buildTrafficSummary($stats, $interfaces, $timeframe);
            
            // Get AI analysis
            $aiAnalysis = $this->getAIAnalysis($summary);
            
            return [
                'status' => 'success',
                'timeframe' => $timeframe,
                'summary' => $summary,
                'ai_analysis' => $aiAnalysis,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Traffic analysis failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get traffic history
     */
    public function getHistory(int $hours = 24): array
    {
        try {
            $stats = $this->pfSenseClient->getTrafficStats();
            
            $history = [
                'total_in' => 0,
                'total_out' => 0,
                'peak_in' => 0,
                'peak_out' => 0,
                'average_in' => 0,
                'average_out' => 0,
                'hours' => $hours,
            ];

            return [
                'status' => 'success',
                'history' => $history,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Traffic history failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Detect anomalies
     */
    public function detectAnomalies(): array
    {
        try {
            $stats = $this->pfSenseClient->getTrafficStats();
            
            $anomalies = [];
            // Implement anomaly detection logic
            
            $prompt = "Analyze these network traffic anomalies for pfSense firewall: " . json_encode($anomalies);
            $aiAnalysis = $this->aiFactory->chat($prompt, ['role' => 'security_analyst']);
            
            return [
                'status' => 'success',
                'anomalies_detected' => count($anomalies),
                'details' => $anomalies,
                'ai_insight' => $aiAnalysis,
            ];
        } catch (\Exception $e) {
            $this->logger->error('Anomaly detection failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    private function buildTrafficSummary(array $stats, array $interfaces, string $timeframe): array
    {
        return [
            'interfaces_monitored' => count($interfaces),
            'total_packets' => $stats['packets'] ?? 0,
            'total_bytes' => $stats['bytes'] ?? 0,
            'timeframe' => $timeframe,
            'data' => $stats,
        ];
    }

    private function getAIAnalysis(array $summary): string
    {
        $prompt = "Provide a brief analysis of this network traffic summary: " . json_encode($summary);
        return $this->aiFactory->chat($prompt, ['role' => 'network_analyst']);
    }
}
