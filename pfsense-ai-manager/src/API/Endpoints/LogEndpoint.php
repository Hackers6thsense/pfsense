<?php
/**
 * Log Endpoint
 */

namespace PfSenseAI\API\Endpoints;

use PfSenseAI\Analysis\LogAnalyzer;
use PfSenseAI\API\Router;

class LogEndpoint extends Router
{
    public function getLogs()
    {
        try {
            $input = self::getInput();
            $filter = $_GET['filter'] ?? '';
            $limit = $_GET['limit'] ?? 100;

            $analyzer = new LogAnalyzer();
            $result = $analyzer->analyzeLogs($filter, (int)$limit);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function analyze()
    {
        try {
            $input = self::getInput();
            $filter = $input['filter'] ?? '';
            $limit = $input['limit'] ?? 100;

            $analyzer = new LogAnalyzer();
            $result = $analyzer->analyzeLogs($filter, $limit);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function search()
    {
        try {
            $input = self::getInput();
            $query = $input['query'] ?? '';

            if (empty($query)) {
                self::response(['error' => 'Query required'], 400);
                return;
            }

            $analyzer = new LogAnalyzer();
            $result = $analyzer->nlSearch($query);

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function getPatterns()
    {
        try {
            $analyzer = new LogAnalyzer();
            $result = $analyzer->getPatterns();

            self::response($result);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }
}
