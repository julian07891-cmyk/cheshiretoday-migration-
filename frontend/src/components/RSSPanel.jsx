import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Rss, RefreshCw, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import { getApiUrl } from '../utils/api';

const BACKEND_URL = getApiUrl();

const RSSPanel = ({ onArticlesImported }) => {
  const [importing, setImporting] = useState(false);
  const [sources, setSources] = useState([]);
  const [loadingSources, setLoadingSources] = useState(false);

  const loadRSSSources = async () => {
    try {
      setLoadingSources(true);
      const response = await fetch(`${BACKEND_URL}/api/rss-sources`);
      const data = await response.json();
      setSources(data.sources || []);
    } catch (error) {
      console.error('Error loading RSS sources:', error);
      toast({
        title: "Error",
        description: "Failed to load RSS sources",
        variant: "destructive"
      });
    } finally {
      setLoadingSources(false);
    }
  };

  React.useEffect(() => {
    loadRSSSources();
  }, []);

  const importRSSArticles = async (category = null) => {
    try {
      setImporting(true);

      const url = new URL(
        "/api/import-rss",
        BACKEND_URL
      );
      if (category) {
        url.searchParams.append('category', category);
      }
      url.searchParams.append('max_per_source', '3');
      url.searchParams.append('use_ai', 'true');

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to import articles');
      }

      const data = await response.json();
      
      toast({
        title: "Success!",
        description: data.message,
      });

      if (onArticlesImported) {
        onArticlesImported();
      }
    } catch (error) {
      console.error('Error importing RSS articles:', error);
      toast({
        title: "Error",
        description: "Failed to import RSS articles. Please try again.",
        variant: "destructive"
      });
    } finally {
      setImporting(false);
    }
  };

  const getRSSFeedUrl = () => {
    return `${BACKEND_URL}/api/feed.xml`;
  };

  const copyRSSUrl = () => {
    const url = getRSSFeedUrl();
    navigator.clipboard.writeText(url);
    toast({
      title: "Copied!",
      description: "RSS feed URL copied to clipboard",
    });
  };

  return (
    <div className="space-y-6">
      {/* RSS Feed URL for Subscribers */}
      <Card className="border-2 border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center text-blue-900">
            <Rss className="h-5 w-5 mr-2 text-blue-600" />
            RSS Feed URL
          </CardTitle>
          <CardDescription>
            Subscribe to our RSS feed in your favorite reader
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="bg-white p-3 rounded-md border border-blue-200">
              <code className="text-sm text-gray-700 break-all">
                {getRSSFeedUrl()}
              </code>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={copyRSSUrl}
                variant="outline"
                className="hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
              >
                Copy URL
              </Button>
              <Button 
                onClick={() => window.open(getRSSFeedUrl(), '_blank')}
                variant="outline"
                className="hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
              >
                View Feed
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Import from RSS Sources */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <RefreshCw className="h-5 w-5 mr-2 text-blue-600" />
            Import from External Sources
          </CardTitle>
          <CardDescription>
            Fetch and rewrite articles from external RSS feeds using AI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Available Sources ({sources.length} feeds):</p>
              {loadingSources ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                </div>
              ) : (
                <div className="max-h-64 overflow-y-auto space-y-2 pr-2">
                  {sources.map((source, index) => (
                    <div 
                      key={index}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded border text-xs hover:bg-gray-100 transition-colors"
                    >
                      <span className="font-medium text-gray-800 truncate flex-1">{source.name}</span>
                      <Badge variant="outline" className="text-xs ml-2 flex-shrink-0">
                        {source.category}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
              <div className="bg-blue-50 border border-blue-200 rounded p-3 text-xs text-blue-800">
                <p className="font-medium mb-1">Coverage includes:</p>
                <p>Cheshire, Manchester, Liverpool & Golden Triangle region</p>
              </div>
            </div>

            <div className="pt-4 border-t">
              <Button 
                onClick={() => importRSSArticles()}
                disabled={importing}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {importing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importing & Processing with AI...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Import Articles Now
                  </>
                )}
              </Button>
              <p className="text-xs text-gray-500 mt-2 text-center">
                Articles will be rewritten using Perplexity AI for Cheshire context
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="space-y-2">
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-blue-600 mr-2 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900">Automatic Content Generation</p>
                <p className="text-xs text-blue-700 mt-1">
                  Fresh articles imported daily. The Daily Brief email sent at 7:30 AM
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-blue-600 mr-2 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900">AI-Powered Rewriting</p>
                <p className="text-xs text-blue-700 mt-1">
                  External articles are localized for Cheshire readers using Perplexity AI
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RSSPanel;
