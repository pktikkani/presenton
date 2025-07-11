"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

export default function V2TestPage() {
  const [prompt, setPrompt] = useState('Create a presentation about renewable energy sources');
  const [model, setModel] = useState('');
  const [slides, setSlides] = useState('5');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  // Fetch available models
  const fetchModels = async () => {
    setLoadingModels(true);
    try {
      const res = await fetch('/api/v2/ppt/models', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (res.ok) {
        const data = await res.json();
        setAvailableModels(data.models || []);
        toast({
          title: "Models loaded",
          description: `Found ${data.models?.length || 0} available models`,
        });
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
      toast({
        title: "Error",
        description: "Failed to load available models",
        variant: "destructive",
      });
    } finally {
      setLoadingModels(false);
    }
  };

  // Test presentation generation
  const testGeneration = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const requestData = {
        prompt,
        n_slides: parseInt(slides),
        language: "English",
        slide_mode: "normal",
        model: model || undefined,
      };

      const res = await fetch('/api/v2/ppt/generate/presentation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Generation failed');
      }

      setResponse(data);
      toast({
        title: "Success!",
        description: "Presentation generated successfully with PydanticAI",
      });
    } catch (err: any) {
      setError(err.message);
      toast({
        title: "Error",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-10 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-600" />
            V2 API Test - PydanticAI Integration
          </CardTitle>
          <CardDescription>
            Test the new V2 endpoints with PydanticAI structured output validation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Model Selection */}
          <div className="space-y-2">
            <Label>Model Selection</Label>
            <div className="flex gap-2">
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Select a model (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Default</SelectItem>
                  {availableModels.map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button 
                onClick={fetchModels} 
                variant="outline"
                disabled={loadingModels}
              >
                {loadingModels ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Load Models"
                )}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Leave empty to use default model
            </p>
          </div>

          {/* Prompt */}
          <div className="space-y-2">
            <Label htmlFor="prompt">Prompt</Label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your presentation topic..."
              className="min-h-[100px]"
            />
          </div>

          {/* Number of slides */}
          <div className="space-y-2">
            <Label htmlFor="slides">Number of Slides</Label>
            <Input
              id="slides"
              type="number"
              value={slides}
              onChange={(e) => setSlides(e.target.value)}
              min="3"
              max="20"
            />
          </div>

          {/* Generate Button */}
          <Button
            onClick={testGeneration}
            disabled={loading || !prompt}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating with PydanticAI...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Presentation
              </>
            )}
          </Button>

          {/* Error Display */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-red-900">Error</h4>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Response Display */}
          {response && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="h-5 w-5" />
                <h3 className="font-medium">Generation Successful!</h3>
              </div>
              
              <div className="rounded-lg border bg-muted/50 p-4">
                <h4 className="font-medium mb-2">Response Details:</h4>
                <dl className="space-y-1 text-sm">
                  <div className="flex gap-2">
                    <dt className="font-medium">ID:</dt>
                    <dd className="font-mono">{response.id}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="font-medium">Title:</dt>
                    <dd>{response.title}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="font-medium">Slides:</dt>
                    <dd>{response.slides?.length || 0}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="font-medium">Theme:</dt>
                    <dd>{response.theme}</dd>
                  </div>
                </dl>
              </div>

              {/* Slides Preview */}
              {response.slides && response.slides.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium">Generated Slides:</h4>
                  {response.slides.slice(0, 3).map((slide: any, idx: number) => (
                    <div key={idx} className="rounded-lg border p-3">
                      <h5 className="font-medium text-sm">
                        Slide {idx + 1}: {slide.title}
                      </h5>
                      <p className="text-sm text-muted-foreground mt-1">
                        Type: {slide.slide_type} | Items: {slide.content?.body?.length || 0}
                      </p>
                    </div>
                  ))}
                  {response.slides.length > 3 && (
                    <p className="text-sm text-muted-foreground">
                      ... and {response.slides.length - 3} more slides
                    </p>
                  )}
                </div>
              )}

              {/* Raw JSON */}
              <details className="cursor-pointer">
                <summary className="text-sm font-medium">View Raw JSON</summary>
                <pre className="mt-2 rounded-lg bg-muted p-3 text-xs overflow-auto">
                  {JSON.stringify(response, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}