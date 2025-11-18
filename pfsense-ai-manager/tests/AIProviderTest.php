<?php
/**
 * Unit Tests for AI Providers
 */

use PHPUnit\Framework\TestCase;
use PfSenseAI\AI\MistralProvider;
use PfSenseAI\AI\GroqProvider;
use PfSenseAI\AI\GeminiProvider;
use PfSenseAI\AI\AIFactory;

class AIProviderTest extends TestCase
{
    public function testMistralProviderInitialization()
    {
        $provider = new MistralProvider();
        $info = $provider->getModelInfo();
        
        $this->assertEquals('mistral', $info['provider']);
        $this->assertIsArray($info);
    }

    public function testGroqProviderInitialization()
    {
        $provider = new GroqProvider();
        $info = $provider->getModelInfo();
        
        $this->assertEquals('groq', $info['provider']);
        $this->assertIsArray($info);
    }

    public function testGeminiProviderInitialization()
    {
        $provider = new GeminiProvider();
        $info = $provider->getModelInfo();
        
        $this->assertEquals('gemini', $info['provider']);
        $this->assertIsArray($info);
    }

    public function testAIFactory()
    {
        $factory = AIFactory::getInstance();
        $this->assertNotNull($factory);
    }
}
