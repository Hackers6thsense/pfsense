<?php
/**
 * Logger Utility
 */

namespace PfSenseAI\Utils;

class Logger
{
    private static $instance;
    private $logFile;
    private $logLevel = 'info';

    private const LOG_LEVELS = [
        'debug' => 0,
        'info' => 1,
        'warning' => 2,
        'error' => 3,
        'critical' => 4,
    ];

    public function __construct()
    {
        $config = Config::getInstance();
        $this->logFile = BASE_PATH . '/logs/pfsense-ai.log';
        $this->logLevel = $config->get('app.log_level', 'info');

        if (!is_dir(dirname($this->logFile))) {
            mkdir(dirname($this->logFile), 0755, true);
        }
    }

    public static function getInstance()
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    public function log($level, $message, $context = [])
    {
        if (self::LOG_LEVELS[$level] < self::LOG_LEVELS[$this->logLevel]) {
            return;
        }

        $timestamp = date('Y-m-d H:i:s');
        $logMessage = sprintf(
            '[%s] %s: %s',
            $timestamp,
            strtoupper($level),
            $this->interpolate($message, $context)
        );

        error_log($logMessage . PHP_EOL, 3, $this->logFile);
    }

    public function debug($message, $context = [])
    {
        $this->log('debug', $message, $context);
    }

    public function info($message, $context = [])
    {
        $this->log('info', $message, $context);
    }

    public function warning($message, $context = [])
    {
        $this->log('warning', $message, $context);
    }

    public function error($message, $context = [])
    {
        $this->log('error', $message, $context);
    }

    public function critical($message, $context = [])
    {
        $this->log('critical', $message, $context);
    }

    private function interpolate($message, $context)
    {
        $replace = [];
        foreach ($context as $key => $value) {
            if (!is_array($value) && (!is_object($value) || method_exists($value, '__toString'))) {
                $replace['{' . $key . '}'] = $value;
            }
        }
        return strtr($message, $replace);
    }
}
