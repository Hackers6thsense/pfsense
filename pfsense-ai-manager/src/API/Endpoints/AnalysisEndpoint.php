<?php
/**
 * Analysis Endpoint
 */

namespace PfSenseAI\API\Endpoints;

use PfSenseAI\Analysis\TrafficAnalyzer;
use PfSenseAI\API\Router;

class AnalysisEndpoint extends Router
{
    public function analyzeTraffic()
    {
        try {
            $input = self::getInput();
            $timeframe = $input['timeframe'] ?? 'last_hour';

            $analyzer = new TrafficAnalyzer();
            $result = $analyzer->analyze($timeframe);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function getTrafficHistory()
    {
        try {
            $input = self::getInput();
            $hours = $input['hours'] ?? 24;

            $analyzer = new TrafficAnalyzer();
            $result = $analyzer->getHistory($hours);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function detectAnomalies()
    {
        try {
            $analyzer = new TrafficAnalyzer();
            $result = $analyzer->detectAnomalies();

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }
}
