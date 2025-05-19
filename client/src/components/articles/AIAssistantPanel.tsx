import { useState } from 'react';
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
  ChevronRight,
  ChevronLeft,
  X,
  Pencil,
  Book
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIAssistantPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onInsertContent: (content: string) => void;
  className?: string;
}

export function AIAssistantPanel({ 
  isOpen, 
  onClose, 
  onInsertContent,
  className 
}: AIAssistantPanelProps) {
  // UI State
  const [activeTab, setActiveTab] = useState<string>('draft');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [generatedContent, setGeneratedContent] = useState<string>('');
  
  // Form state
  const [draftTopic, setDraftTopic] = useState<string>('');
  const [draftOutline, setDraftOutline] = useState<string>('');
  const [draftLength, setDraftLength] = useState<string>('medium');
  const [draftStyle, setDraftStyle] = useState<string>('informative');

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
      
      const response = await fetch('/api/llm/draft-article', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          topic: draftTopic,
          outline: outlinePoints.length > 0 ? outlinePoints : undefined,
          length: draftLength,
          style: draftStyle
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      setGeneratedContent(data.draft);
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
      onInsertContent(generatedContent);
      // Optionally clear the generated content after insertion
      // setGeneratedContent('');
    }
  };

  // Handle clearing the form
  const handleClearForm = () => {
    setDraftTopic('');
    setDraftOutline('');
    setGeneratedContent('');
  };

  return (
    <div className={cn(
      "fixed top-0 bottom-0 right-0 w-96 bg-background border-l shadow-lg transition-transform duration-200 ease-in-out z-50 flex flex-col",
      isOpen ? "translate-x-0" : "translate-x-full",
      className
    )}>
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-medium">AI Assistant</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="w-4 h-4" />
        </Button>
      </div>
      
      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto p-4">
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
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="topic" className="text-sm font-medium">Topic</label>
                    <Input
                      id="topic"
                      placeholder="Enter the main topic of your article"
                      value={draftTopic}
                      onChange={(e) => setDraftTopic(e.target.value)}
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
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label htmlFor="length" className="text-sm font-medium">Length</label>
                      <Select
                        value={draftLength}
                        onValueChange={setDraftLength}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select length" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="short">Short (~500 words)</SelectItem>
                          <SelectItem value="medium">Medium (~1000 words)</SelectItem>
                          <SelectItem value="long">Long (~2000 words)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="style" className="text-sm font-medium">Writing Style</label>
                      <Select
                        value={draftStyle}
                        onValueChange={setDraftStyle}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select style" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="informative">Informative</SelectItem>
                          <SelectItem value="conversational">Conversational</SelectItem>
                          <SelectItem value="persuasive">Persuasive</SelectItem>
                          <SelectItem value="technical">Technical</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline" onClick={handleClearForm}>
                    Clear
                  </Button>
                  <Button 
                    onClick={handleGenerateDraft} 
                    disabled={!draftTopic.trim() || isLoading}
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
                  <div className="bg-muted/30 rounded-md p-4 max-h-[500px] overflow-y-auto">
                    {generatedContent.split('\n').map((line, i) => (
                      <p key={i} className={i !== 0 ? "mt-2" : ""}>
                        {line || <br />}
                      </p>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline" onClick={() => setGeneratedContent('')}>
                    <X className="mr-2 h-4 w-4" />
                    Discard
                  </Button>
                  <Button onClick={handleInsertContent}>
                    <ChevronLeft className="mr-2 h-4 w-4" />
                    Insert into Editor
                  </Button>
                </CardFooter>
              </Card>
            )}
          </TabsContent>
          
          {/* Additional Writing Tools Tab (placeholder for future features) */}
          <TabsContent value="tools">
            <Card>
              <CardHeader>
                <CardTitle>Writing Tools</CardTitle>
                <CardDescription>
                  More AI-powered writing tools will be available soon
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center py-8 text-muted-foreground">
                <Book className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Coming Soon</p>
                <p className="text-sm mt-2">
                  Additional AI tools for enhancing your writing will appear here
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Panel toggle button (visible when closed) */}
      {!isOpen && (
        <Button 
          variant="outline" 
          size="icon"
          className="absolute top-4 -left-12 h-10 w-10 rounded-l-lg border-r-0"
          onClick={onClose}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
} 