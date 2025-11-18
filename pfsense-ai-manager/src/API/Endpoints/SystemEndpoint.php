<?php
/**
 * System Endpoint
 */

namespace PfSenseAI\API\Endpoints;

use PfSenseAI\AI\AIFactory;
use PfSenseAI\API\Router;

class SystemEndpoint extends Router
{
    public function status()
    {
        try {
            $aiFactory = AIFactory::getInstance();

            self::response([
                'status' => 'success',
                'application' => 'pfSense AI Manager',
                'version' => '1.0.0',
                'current_provider' => $aiFactory->getCurrentProviderName(),
                'available_providers' => $aiFactory->getAvailableProviders(),
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }

    public function getProviders()
    {
        try {
            $aiFactory = AIFactory::getInstance();

            self::response([
                'status' => 'success',
                'providers' => $aiFactory->getAvailableProviders(),
                'timestamp' => date('Y-m-d H:i:s'),
            ]);
        } catch (\Exception $e) {
            self::response(['error' => $e->getMessage()], 500);
        }
    }
}
