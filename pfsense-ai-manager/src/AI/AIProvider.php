<?php
/**
 * AI Provider Interface
 */

namespace PfSenseAI\AI;

interface AIProvider
{
    /**
     * Send a message to the AI and get a response
     *
     * @param string $message The user message
     * @param array $context Additional context for the AI
     * @return string The AI response
     */
    public function chat(string $message, array $context = []): string;

    /**
     * Analyze content with the AI
     *
     * @param string $content Content to analyze
     * @param string $type Type of analysis (e.g., 'threat', 'traffic', 'log')
     * @return array Analysis results
     */
    public function analyze(string $content, string $type = 'general'): array;

    /**
     * Get model information
     *
     * @return array Model details
     */
    public function getModelInfo(): array;

    /**
     * Check if the provider is available
     *
     * @return bool
     */
    public function isAvailable(): bool;
}
