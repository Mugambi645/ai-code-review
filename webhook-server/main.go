package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/google/go-github/v62/github"
	"golang.org/x/oauth2"
)

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	// Health check
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
	})

	// Test go-github + oauth2: fetch a public repo (no token needed)
	r.Get("/test-github", func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()

		// oauth2 token source (empty = unauthenticated, fine for public repos)
		ts := oauth2.StaticTokenSource(&oauth2.Token{AccessToken: ""})
		tc := oauth2.NewClient(ctx, ts)
		client := github.NewClient(tc)

		repo, _, err := client.Repositories.Get(ctx, "go-chi", "chi")
		if err != nil {
			http.Error(w, fmt.Sprintf("github error: %v", err), http.StatusInternalServerError)
			return
		}

		json.NewEncoder(w).Encode(map[string]any{
			"repo":  repo.GetFullName(),
			"stars": repo.GetStargazersCount(),
			"url":   repo.GetHTMLURL(),
		})
	})

	log.Println("webhook-server running on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}
