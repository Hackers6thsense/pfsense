<?php
/**
 * Configuration Endpoint
 */

namespace PfSenseAI\API\Endpoints;

use PfSenseAI\Analysis\ConfigAnalyzer;
use PfSenseAI\API\Router;

class ConfigEndpoint extends Router
{
    public function getRules()
    {
        try {
            $analyzer = new ConfigAnalyzer();
            $result = $analyzer->analyze();

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function analyze()
    {
        try {
            $analyzer = new ConfigAnalyzer();
            $result = $analyzer->analyze();

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function getRecommendations()
    {
        try {
            $input = self::getInput();
            $type = $input['type'] ?? 'security';

            $analyzer = new ConfigAnalyzer();
            $result = $analyzer->getRecommendations($type);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }
}
