<?php
/**
 * Threat Endpoint
 */

namespace PfSenseAI\API\Endpoints;

use PfSenseAI\Analysis\ThreatDetector;
use PfSenseAI\API\Router;

class ThreatEndpoint extends Router
{
    public function getThreats()
    {
        try {
            $detector = new ThreatDetector();
            $result = $detector->detectThreats();

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function analyzeThreat()
    {
        try {
            $input = self::getInput();
            $threatData = $input['threat'] ?? [];

            if (empty($threatData)) {
                self::response(['error' => 'Threat data required'], 400);
                return;
            }

            $detector = new ThreatDetector();
            $result = $detector->analyzeThreat($threatData);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function getDashboard()
    {
        try {
            $detector = new ThreatDetector();
            $result = $detector->getDashboard();

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }
}
