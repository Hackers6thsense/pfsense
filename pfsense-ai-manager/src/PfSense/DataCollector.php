<?php
/**
 * Data Collector for pfSense metrics
 */

namespace PfSenseAI\PfSense;

use PfSenseAI\Utils\Cache;

class DataCollector
{
    private $client;
    private $cache;

    public function __construct()
    {
        $this->client = new PfSenseClient();
        $this->cache = Cache::getInstance();
    }

    /**
     * Collect all firewall metrics
     */
    public function collectMetrics(): array
    {
        $cacheKey = 'pfsense_metrics';
        
        if ($this->cache->has($cacheKey)) {
            return $this->cache->get($cacheKey);
        }

        $metrics = [
            'system' => $this->client->getStatus(),
            'interfaces' => $this->client->getInterfaces(),
            'rules' => $this->client->getRules(),
            'services' => $this->client->getServices(),
            'traffic' => $this->client->getTrafficStats(),
            'arp_table' => $this->client->getARPTable(),
            'dhcp_leases' => $this->client->getDHCPLeases(),
            'timestamp' => date('Y-m-d H:i:s'),
        ];

        // Cache for 5 minutes
        $this->cache->set($cacheKey, $metrics, 300);

        return $metrics;
    }

    /**
     * Get specific metric
     */
    public function getMetric(string $name): array
    {
        $metrics = $this->collectMetrics();
        return $metrics[$name] ?? [];
    }
}
