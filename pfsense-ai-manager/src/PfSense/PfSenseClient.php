<?php
/**
 * pfSense API Client
 */

namespace PfSenseAI\PfSense;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use PfSenseAI\Utils\Logger;
use PfSenseAI\Utils\Config;

class PfSenseClient
{
    private $client;
    private $baseUrl;
    private $logger;
    private $config;

    public function __construct()
    {
        $this->config = Config::getInstance();
        $this->logger = Logger::getInstance();

        $pfsenseConfig = $this->config->get('pfsense');
        $protocol = 'https'; // pfSense typically uses HTTPS
        $this->baseUrl = "{$protocol}://{$pfsenseConfig['host']}/api";

        $this->client = new Client([
            'base_uri' => $this->baseUrl,
            'timeout' => $pfsenseConfig['timeout'] ?? 30,
            'verify' => $pfsenseConfig['verify_ssl'] ?? false,
            'http_errors' => false,
        ]);
    }

    /**
     * Get authentication headers
     */
    private function getHeaders(): array
    {
        $pfsenseConfig = $this->config->get('pfsense');
        
        if (!empty($pfsenseConfig['api_key'])) {
            return [
                'Authorization' => 'Bearer ' . $pfsenseConfig['api_key'],
                'Content-Type' => 'application/json',
            ];
        }

        // Fallback to basic auth
        $credentials = base64_encode(
            $pfsenseConfig['username'] . ':' . $pfsenseConfig['password']
        );
        return [
            'Authorization' => 'Basic ' . $credentials,
            'Content-Type' => 'application/json',
        ];
    }

    /**
     * Get firewall status
     */
    public function getStatus(): array
    {
        try {
            $response = $this->client->get('system/info', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get pfSense status: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get firewall rules
     */
    public function getRules(): array
    {
        try {
            $response = $this->client->get('firewall/rules', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get firewall rules: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get system logs
     */
    public function getLogs(string $filter = '', int $limit = 100): array
    {
        try {
            $query = '';
            if (!empty($filter)) {
                $query = '?filter=' . urlencode($filter);
            }
            $query .= (strpos($query, '?') ? '&' : '?') . 'limit=' . $limit;

            $response = $this->client->get('system/logs/general' . $query, [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get logs: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get network interfaces
     */
    public function getInterfaces(): array
    {
        try {
            $response = $this->client->get('interface', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get interfaces: {error}', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Get traffic statistics
     */
    public function getTrafficStats(): array
    {
        try {
            $response = $this->client->get('diagnostics/traffic', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get traffic stats: {error}', ['error' => $e->getMessage()]);
            return [];
        }
    }

    /**
     * Get system services status
     */
    public function getServices(): array
    {
        try {
            $response = $this->client->get('services', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get services: {error}', ['error' => $e->getMessage()]);
            return [];
        }
    }

    /**
     * Get DHCP leases
     */
    public function getDHCPLeases(): array
    {
        try {
            $response = $this->client->get('dhcp/leases', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get DHCP leases: {error}', ['error' => $e->getMessage()]);
            return [];
        }
    }

    /**
     * Get ARP table
     */
    public function getARPTable(): array
    {
        try {
            $response = $this->client->get('diagnostics/arp', [
                'headers' => $this->getHeaders(),
            ]);

            return json_decode($response->getBody(), true) ?? [];
        } catch (GuzzleException $e) {
            $this->logger->error('Failed to get ARP table: {error}', ['error' => $e->getMessage()]);
            return [];
        }
    }
}
