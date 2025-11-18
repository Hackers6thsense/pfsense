<?php
/**
 * pfSense AI Manager - Main Entry Point
 */

require_once dirname(__DIR__) . '/src/bootstrap.php';

use PfSenseAI\API\Router;

try {
    $router = new Router();
    $router->dispatch($_SERVER['REQUEST_METHOD'], parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => $e->getMessage(),
        'code' => $e->getCode(),
    ]);
}
