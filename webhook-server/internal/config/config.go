package config

import (
	"os"
)


type Config struct {
	Port              string
	GitHubToken       string
	GitHubWebhookSecret string
	LLMServiceURL     string
}


func Load() *Config {
	return &Config{
		Port:                getEnv("PORT", "8080"),
		GitHubToken:         getEnv("GITHUB_TOKEN", ""),
		GitHubWebhookSecret: getEnv("GITHUB_WEBHOOK_SECRET", ""),
		LLMServiceURL:       getEnv("LLM_SERVICE_URL", "http://localhost:8000"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
