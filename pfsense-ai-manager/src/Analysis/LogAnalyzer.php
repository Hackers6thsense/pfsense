<?php
/**
 * Log Analyzer
 */

namespace PfSenseAI\Analysis;

use PfSenseAI\AI\AIFactory;
use PfSenseAI\PfSense\PfSenseClient;
use PfSenseAI\Utils\Logger;

class LogAnalyzer
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
     * Analyze firewall logs
     */
    public function analyzeLogs(string $filter = '', int $limit = 100): array
    {
        try {
            $logs = $this->pfSenseClient->getLogs($filter, $limit);
            
            $summary = $this->summarizeLogs($logs);
            
            // Get AI analysis
            $aiAnalysis = $this->getAILogAnalysis($logs, $summary);
            
            return [
                'status' => 'success',
                'total_logs' => count($logs),
                'summary' => $summary,
                'ai_analysis' => $aiAnalysis,
                'logs' => array_slice($logs, 0, 20), // Return first 20 for display
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Log analysis failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Search logs with natural language
     */
    public function nlSearch(string $query): array
    {
        try {
            $logs = $this->pfSenseClient->getLogs('', 200);
            
            // Use AI to interpret the natural language query
            $filterPrompt = "Convert this user query into a search filter for pfSense logs: " . $query;
            $aiFilter = $this->aiFactory->chat($filterPrompt, ['role' => 'log_analyst']);
            
            // Filter logs based on AI interpretation
            $filteredLogs = $this->filterLogsByAI($logs, $query);
            
            // Analyze filtered logs
            $analysis = $this->summarizeLogs($filteredLogs);
            
            return [
                'status' => 'success',
                'query' => $query,
                'ai_filter' => $aiFilter,
                'results_found' => count($filteredLogs),
                'summary' => $analysis,
                'logs' => array_slice($filteredLogs, 0, 50),
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('NL search failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get log patterns
     */
    public function getPatterns(): array
    {
        try {
            $logs = $this->pfSenseClient->getLogs('', 500);
            
            $patterns = $this->extractPatterns($logs);
            
            // Get AI insights on patterns
            $aiInsights = $this->getAIPatternInsights($patterns);
            
            return [
                'status' => 'success',
                'patterns_found' => count($patterns),
                'patterns' => $patterns,
                'ai_insights' => $aiInsights,
                'timestamp' => date('Y-m-d H:i:s'),
            ];
        } catch (\Exception $e) {
            $this->logger->error('Pattern extraction failed: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    private function summarizeLogs(array $logs): array
    {
        $summary = [
            'total' => count($logs),
            'by_type' => [],
            'by_severity' => [],
            'timeframe' => [
                'start' => null,
                'end' => null,
            ],
        ];

        foreach ($logs as $log) {
            $type = $log['type'] ?? 'unknown';
            $severity = $log['severity'] ?? 'info';
            
            $summary['by_type'][$type] = ($summary['by_type'][$type] ?? 0) + 1;
            $summary['by_severity'][$severity] = ($summary['by_severity'][$severity] ?? 0) + 1;
        }

        return $summary;
    }

    private function filterLogsByAI(array $logs, string $query): array
    {
        $keywords = preg_split('/\s+/', strtolower($query));
        
        return array_filter($logs, function($log) use ($keywords) {
            $logText = strtolower(json_encode($log));
            foreach ($keywords as $keyword) {
                if (strpos($logText, $keyword) !== false) {
                    return true;
                }
            }
            return false;
        });
    }

    private function extractPatterns(array $logs): array
    {
        $patterns = [];
        $messagePatterns = [];

        foreach ($logs as $log) {
            $msg = $log['msg'] ?? '';
            // Group similar messages
            $pattern = preg_replace('/\d+/', 'N', $msg);
            $messagePatterns[$pattern] = ($messagePatterns[$pattern] ?? 0) + 1;
        }

        // Get top patterns
        arsort($messagePatterns);
        foreach (array_slice($messagePatterns, 0, 20) as $pattern => $count) {
            $patterns[] = [
                'pattern' => $pattern,
                'occurrences' => $count,
            ];
        }

        return $patterns;
    }

    private function getAILogAnalysis(array $logs, array $summary): string
    {
        $analysisPrompt = "Analyze these firewall logs summary: " . json_encode($summary) . 
                          ". Provide key insights and any security concerns.";
        
        return $this->aiFactory->chat($analysisPrompt, ['role' => 'log_analyst']);
    }

    private function getAIPatternInsights(array $patterns): string
    {
        $topPatterns = array_map(function($p) {
            return $p['pattern'] . ' (' . $p['occurrences'] . ' times)';
        }, array_slice($patterns, 0, 10));

        $prompt = "Analyze these log patterns and explain their significance: " . 
                  implode(", ", $topPatterns);
        
        return $this->aiFactory->chat($prompt, ['role' => 'log_analyst']);
    }
}
