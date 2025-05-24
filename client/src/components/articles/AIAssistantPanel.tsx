import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BrainCircuit, 
  Sparkles, 
  Loader2,
  X,
  Pencil,
  Book,
  ChevronLeft
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { llmService, type OllamaModel } from '@/lib/api';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '@/components/ui/tooltip';

interface AIAssistantPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onInsertContent: (content: string, title?: string) => void;
  saveDraft: () => void;
  className?: string;
  onLayoutChange?: (panelWidth: number) => void;
}

export function AIAssistantPanel({ 
  isOpen, 
  onClose, 
  onInsertContent,
  saveDraft,
  className,
  onLayoutChange
}: AIAssistantPanelProps) {
  // UI State
  const [activeTab, setActiveTab] = useState<string>('draft');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [generatedContent, setGeneratedContent] = useState<string>('');
  
  // LLM providers and models state
  const [providers, setProviders] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(false);
  
  // Form state
  const [draftTopic, setDraftTopic] = useState<string>('');
  const [draftOutline, setDraftOutline] = useState<string>('');
  const [draftLength, setDraftLength] = useState<string>('medium');
  const [draftStyle, setDraftStyle] = useState<string>('informative');

  // Effect to notify parent about layout changes
  useEffect(() => {
    if (onLayoutChange) {
      onLayoutChange(isOpen ? 384 : 0); // 384px = w-[384px]
    }
  }, [isOpen, onLayoutChange]);

  // Fetch providers and models on component mount
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const providersData = await llmService.getProviders();
        setProviders(providersData.providers);
        if (providersData.default_provider) {
          setSelectedProvider(providersData.default_provider);
        }
      } catch (error) {
        console.error('Error fetching LLM providers:', error);
      }
    };

    fetchProviders();
  }, []);

  // Fetch Ollama models when provider changes to ollama
  useEffect(() => {
    const fetchOllamaModels = async () => {
      if (selectedProvider === 'ollama') {
        setIsLoadingModels(true);
        try {
          const modelsData = await llmService.getOllamaModels();
          setOllamaModels(modelsData.models);
          // Set default model if available
          if (modelsData.models.length > 0) {
            setSelectedModel(modelsData.models[0].name);
          }
        } catch (error) {
          console.error('Error fetching Ollama models:', error);
        } finally {
          setIsLoadingModels(false);
        }
      }
    };

    fetchOllamaModels();
  }, [selectedProvider]);

  // Handle draft generation
  const handleGenerateDraft = async () => {
    if (!draftTopic.trim()) return;
    
    setIsLoading(true);
    setGeneratedContent('');
    
    try {
      // Parse outline points from text area
      const outlinePoints = draftOutline
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
      
      const result = await llmService.draftArticle(
        draftTopic,
        outlinePoints.length > 0 ? outlinePoints : undefined,
        draftLength,
        draftStyle,
        selectedProvider || undefined,
        selectedModel || undefined
      );
      
      setGeneratedContent(result.draft);
    } catch (error) {
      console.error('Error generating draft:', error);
      // You could add a toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  // Handle inserting the generated content into the editor
  const handleInsertContent = () => {
    if (generatedContent) {
      // Extract title from the first line if it looks like a Markdown heading
      const contentLines = generatedContent.split('\n');
      let title = '';
      let contentWithoutTitle = generatedContent;
      
      // Check if first line is a heading (# or ## format or surrounded by ** or __)
      if (contentLines.length > 0) {
        const firstLine = contentLines[0].trim();
        if (firstLine.startsWith('# ') || firstLine.startsWith('## ')) {
          // Remove the # or ## prefix
          title = firstLine.replace(/^#+\s+/, '');
          
          // Remove the first line from content
          contentWithoutTitle = contentLines.slice(1).join('\n').trim();
        } else if ((firstLine.startsWith('**') && firstLine.endsWith('**')) || 
                  (firstLine.startsWith('__') && firstLine.endsWith('__'))) {
          // Remove the ** or __ wrappers
          title = firstLine.replace(/^\*\*|\*\*$|^__|__$/g, '');
          
          // Remove the first line from content
          contentWithoutTitle = contentLines.slice(1).join('\n').trim();
        }
      }
      
      onInsertContent(contentWithoutTitle, title);
      saveDraft();
    }
  };

  // Handle clearing the form
  const handleClearForm = () => {
    setDraftTopic('');
    setDraftOutline('');
    setGeneratedContent('');
  };

  return (
    <TooltipProvider>
      <div className={cn(
        "fixed top-0 right-0 w-[384px] bg-background border-l shadow-lg z-[99] flex flex-col",
        "h-[100vh] overflow-hidden will-change-transform",
        isOpen ? "translate-x-0" : "translate-x-full opacity-0",
        "transform-gpu", // Use GPU acceleration
        "transition-transform duration-300 ease-in-out", // Apply transition only to transform
        className
      )}>
        {/* Panel Header */}
        <div className="flex items-center justify-between border-b p-4 bg-muted/10 sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-medium">AI Assistant</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="hover:bg-muted">
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Panel Content */}
        <div className="flex-1 overflow-y-auto p-4 h-[calc(100vh-64px)]">
          <Tabs defaultValue="draft" value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-4 w-full">
              <TabsTrigger value="draft" className="flex-1">
                <Pencil className="w-4 h-4 mr-2" />
                Article Draft
              </TabsTrigger>
              <TabsTrigger value="tools" className="flex-1">
                <Sparkles className="w-4 h-4 mr-2" />
                Writing Tools
              </TabsTrigger>
            </TabsList>
            
            {/* Draft Generation Tab */}
            <TabsContent value="draft" className="space-y-4">
              {!generatedContent ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Generate Article Draft</CardTitle>
                    <CardDescription>
                      Create an AI-generated article draft based on your topic
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* AI Provider and Model Selection */}
                    <div>
                      <h3 className="text-sm font-semibold mb-3 pb-1 border-b">AI Model</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label htmlFor="provider" className="text-sm font-medium">AI Provider</label>
                          <Select
                            value={selectedProvider}
                            onValueChange={setSelectedProvider}
                            disabled={providers.length === 0}
                          >
                            <SelectTrigger 
                              className="h-9 hover:border-primary focus:ring-1 focus:ring-primary"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <SelectValue placeholder="Select provider" />
                            </SelectTrigger>
                            <SelectContent 
                              position="popper" 
                              sideOffset={5}
                              className="z-[200]"
                            >
                              {providers.map(provider => (
                                <SelectItem 
                                  key={provider} 
                                  value={provider}
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {provider.charAt(0).toUpperCase() + provider.slice(1)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-2">
                          <label htmlFor="model" className="text-sm font-medium">Model</label>
                          <Select
                            value={selectedModel}
                            onValueChange={setSelectedModel}
                            disabled={selectedProvider !== 'ollama' || isLoadingModels || ollamaModels.length === 0}
                          >
                            <SelectTrigger 
                              className="h-9 hover:border-primary focus:ring-1 focus:ring-primary"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {isLoadingModels ? (
                                <div className="flex items-center">
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  <span>Loading...</span>
                                </div>
                              ) : (
                                <SelectValue placeholder="Select model" />
                              )}
                            </SelectTrigger>
                            <SelectContent 
                              position="popper" 
                              sideOffset={5}
                              className="z-[200]"
                            >
                              {ollamaModels.map(model => (
                                <SelectItem 
                                  key={model.name} 
                                  value={model.name}
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {model.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold mb-3 pb-1 border-b">Article Content</h3>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <label htmlFor="topic" className="text-sm font-medium">Topic</label>
                          <Input
                            id="topic"
                            placeholder="Enter the main topic of your article"
                            value={draftTopic}
                            onChange={(e) => setDraftTopic(e.target.value)}
                            className="h-9 transition-all hover:border-primary focus:ring-1 focus:ring-primary"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <label htmlFor="outline" className="text-sm font-medium">Outline (Optional)</label>
                          <Textarea
                            id="outline"
                            placeholder="Enter outline points, one per line"
                            value={draftOutline}
                            onChange={(e) => setDraftOutline(e.target.value)}
                            rows={4}
                            className="min-h-[100px] resize-y transition-all hover:border-primary focus:ring-1 focus:ring-primary"
                          />
                        </div>
                      </div>
                    </div>
                    
                    {/* Length and Writing Style controls */}
                    <div>
                      <h3 className="text-sm font-semibold mb-3 pb-1 border-b">Article Parameters</h3>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <label htmlFor="length" className="text-sm font-medium">Length</label>
                          <Select
                            value={draftLength}
                            onValueChange={setDraftLength}
                          >
                            <SelectTrigger 
                              className="h-9 hover:border-primary focus:ring-1 focus:ring-primary"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <SelectValue placeholder="Select length" />
                            </SelectTrigger>
                            <SelectContent 
                              position="popper" 
                              sideOffset={5}
                              className="z-[200]"
                            >
                              <SelectItem value="short" onClick={(e) => e.stopPropagation()}>Short (~500 words)</SelectItem>
                              <SelectItem value="medium" onClick={(e) => e.stopPropagation()}>Medium (~1000 words)</SelectItem>
                              <SelectItem value="long" onClick={(e) => e.stopPropagation()}>Long (~2000 words)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-2">
                          <label htmlFor="style" className="text-sm font-medium">Writing Style</label>
                          <Select
                            value={draftStyle}
                            onValueChange={setDraftStyle}
                          >
                            <SelectTrigger 
                              className="h-9 hover:border-primary focus:ring-1 focus:ring-primary"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <SelectValue placeholder="Select style" />
                            </SelectTrigger>
                            <SelectContent 
                              position="popper" 
                              sideOffset={5}
                              className="z-[200]"
                            >
                              <SelectItem value="informative" onClick={(e) => e.stopPropagation()}>Informative</SelectItem>
                              <SelectItem value="conversational" onClick={(e) => e.stopPropagation()}>Conversational</SelectItem>
                              <SelectItem value="persuasive" onClick={(e) => e.stopPropagation()}>Persuasive</SelectItem>
                              <SelectItem value="technical" onClick={(e) => e.stopPropagation()}>Technical</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between pt-2 border-t">
                    <Button variant="outline" onClick={handleClearForm}>
                      Clear
                    </Button>
                    <Button 
                      onClick={handleGenerateDraft} 
                      disabled={!draftTopic.trim() || isLoading}
                      className="transition-all hover:bg-primary/90"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Generate Draft
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </Card>
              ) : (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex justify-between items-center">
                      Draft Preview
                      <Button variant="ghost" size="sm" onClick={() => setGeneratedContent('')}>
                        <X className="w-4 h-4 mr-2" />
                        Close
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted/30 rounded-md p-4 max-h-[500px] overflow-y-auto border">
                      {generatedContent.split('\n').map((line, i) => (
                        <p key={i} className={i !== 0 ? "mt-2" : ""}>
                          {line}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter className="border-t pt-3">
                    <Button 
                      onClick={handleInsertContent} 
                      className="w-full transition-all hover:bg-primary/90 gap-2"
                    >
                      <Book className="h-4 w-4" />
                      Insert into Editor
                    </Button>
                  </CardFooter>
                </Card>
              )}
            </TabsContent>
            
            {/* Writing Tools Tab */}
            <TabsContent value="tools">
              <Card>
                <CardHeader>
                  <CardTitle>Writing Tools</CardTitle>
                  <CardDescription>
                    AI-powered tools to enhance your writing
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    More writing tools will be available in future updates.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Panel toggle button (visible when closed) */}
        {!isOpen && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="outline" 
                size="icon"
                className="fixed top-20 right-0 h-10 w-10 rounded-l-lg border-r-0 shadow-md z-[100] bg-background hover:translate-x-1 transition-transform duration-200"
                onClick={onClose} 
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p>Show AI Assistant</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
} 