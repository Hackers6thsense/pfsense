<?php
/**
 * Cache Utility for storing analysis results
 */

namespace PfSenseAI\Utils;

class Cache
{
    private static $instance;
    private $cacheDir;
    private $ttl = 3600; // 1 hour default

    public function __construct()
    {
        $this->cacheDir = BASE_PATH . '/storage/cache';
        if (!is_dir($this->cacheDir)) {
            mkdir($this->cacheDir, 0755, true);
        }
    }

    public static function getInstance()
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    public function set(string $key, $value, int $ttl = null)
    {
        $ttl = $ttl ?? $this->ttl;
        $data = [
            'value' => $value,
            'expires' => time() + $ttl,
        ];

        $file = $this->getFilePath($key);
        file_put_contents($file, json_encode($data));
    }

    public function get(string $key, $default = null)
    {
        $file = $this->getFilePath($key);

        if (!file_exists($file)) {
            return $default;
        }

        $data = json_decode(file_get_contents($file), true);

        if ($data['expires'] < time()) {
            unlink($file);
            return $default;
        }

        return $data['value'];
    }

    public function has(string $key): bool
    {
        return $this->get($key) !== null;
    }

    public function forget(string $key)
    {
        $file = $this->getFilePath($key);
        if (file_exists($file)) {
            unlink($file);
        }
    }

    public function flush()
    {
        $files = glob($this->cacheDir . '/*');
        foreach ($files as $file) {
            if (is_file($file)) {
                unlink($file);
            }
        }
    }

    private function getFilePath(string $key): string
    {
        $filename = md5($key) . '.cache';
        return $this->cacheDir . '/' . $filename;
    }
}
