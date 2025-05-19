import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ImageUpload } from '@/components/ui/image-upload';
import { Card, CardContent } from '@/components/ui/card';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import {
  Bold,
  Italic,
  Link,
  List,
  ListOrdered,
  Image as ImageIcon,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Heading1,
  Heading2,
  Code,
  Quote,
  Eye,
  Edit,
  Table,
  BrainCircuit,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { AIAssistantPanel } from './AIAssistantPanel';

interface RichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  placeholder?: string;
}

// Configure marked for security
marked.setOptions({
  gfm: true,
  breaks: true,
  // 'sanitize' option is deprecated in newer versions of marked
  // We'll use DOMPurify for sanitization instead
});

export function RichTextEditor({ value, onChange, className, placeholder }: RichTextEditorProps) {
  const [activeTab, setActiveTab] = useState<string>('edit');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showImageDropdown, setShowImageDropdown] = useState<boolean>(false);
  const [imageAlignment, setImageAlignment] = useState<'left' | 'center' | 'right'>('center');
  const [imageSize, setImageSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [renderedHTML, setRenderedHTML] = useState<string>('');
  const [isAssistantOpen, setIsAssistantOpen] = useState<boolean>(false);
  
  // Update rendered HTML when content or tab changes
  useEffect(() => {
    if (activeTab === 'preview') {
      // Use marked to convert markdown to HTML, then sanitize
      const html = marked(value);
      if (typeof html === 'string') {
        setRenderedHTML(DOMPurify.sanitize(html));
      } else {
        // If it's a Promise, handle it when resolved
        Promise.resolve(html)
          .then(resolvedHtml => setRenderedHTML(DOMPurify.sanitize(resolvedHtml)))
          .catch(err => console.error('Error rendering markdown:', err));
      }
    }
  }, [value, activeTab]);

  // Get cursor position to insert at that position
  const getCursorPosition = (): number => {
    if (!textareaRef.current) return 0;
    return textareaRef.current.selectionStart;
  };

  // Set cursor position after insertion
  const setCursorPosition = (position: number) => {
    if (!textareaRef.current) return;
    textareaRef.current.focus();
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.selectionStart = position;
        textareaRef.current.selectionEnd = position;
      }
    }, 0);
  };

  // Insert text at cursor position
  const insertAtCursor = (textToInsert: string) => {
    if (!textareaRef.current) return;
    
    const cursorPos = getCursorPosition();
    const textBefore = value.substring(0, cursorPos);
    const textAfter = value.substring(cursorPos);
    
    const newValue = textBefore + textToInsert + textAfter;
    onChange(newValue);
    
    // Set cursor position after insertion
    const newCursorPos = cursorPos + textToInsert.length;
    setCursorPosition(newCursorPos);
  };

  // Handle image upload
  const handleImageUploaded = (imageUrl: string) => {
    let imageMarkdown = '';
    
    // Create HTML for image based on alignment and size
    switch (imageAlignment) {
      case 'left':
        imageMarkdown = `<img src="${imageUrl}" alt="Image" style="float: left; margin-right: 10px; ${getSizeStyle(imageSize)}" />`;
        break;
      case 'center':
        imageMarkdown = `<div style="text-align: center;"><img src="${imageUrl}" alt="Image" style="${getSizeStyle(imageSize)}" /></div>`;
        break;
      case 'right':
        imageMarkdown = `<img src="${imageUrl}" alt="Image" style="float: right; margin-left: 10px; ${getSizeStyle(imageSize)}" />`;
        break;
      default:
        imageMarkdown = `![Image](${imageUrl})`;
    }
    
    insertAtCursor(imageMarkdown);
    setShowImageDropdown(false);
  };

  const getSizeStyle = (size: string): string => {
    switch (size) {
      case 'small':
        return 'width: 25%;';
      case 'medium':
        return 'width: 50%;';
      case 'large':
        return 'width: 100%;';
      default:
        return 'width: 50%;';
    }
  };

  // Toggle the AI Assistant panel
  const toggleAssistantPanel = () => {
    setIsAssistantOpen(prev => !prev);
  };

  // Handle content insertion from AI Assistant
  const handleInsertFromAssistant = (content: string) => {
    // Switch to edit tab if in preview mode
    if (activeTab === 'preview') {
      setActiveTab('edit');
    }
    
    // Insert the content at the current cursor position
    insertAtCursor(content);
    
    // Optionally close the assistant panel after insertion
    // setIsAssistantOpen(false);
  };

  // Toolbar actions
  const actions = {
    bold: () => insertAtCursor('**Bold Text**'),
    italic: () => insertAtCursor('*Italic Text*'),
    link: () => insertAtCursor('[Link Text](https://)'),
    listBullet: () => insertAtCursor('\n- List item\n- List item\n- List item\n'),
    listOrdered: () => insertAtCursor('\n1. List item\n2. List item\n3. List item\n'),
    heading1: () => insertAtCursor('\n# Heading 1\n'),
    heading2: () => insertAtCursor('\n## Heading 2\n'),
    code: () => insertAtCursor('\n```\ncode block\n```\n'),
    quote: () => insertAtCursor('\n> Blockquote\n'),
    table: () => insertAtCursor('\n| Header 1 | Header 2 | Header 3 |\n| --- | --- | --- |\n| Cell 1 | Cell 2 | Cell 3 |\n| Cell 4 | Cell 5 | Cell 6 |\n'),
  };

  return (
    <div className={cn("space-y-2", className)}>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="flex justify-between items-center mb-2">
          <TabsList>
            <TabsTrigger value="edit" className="flex items-center gap-1">
              <Edit className="h-4 w-4" />
              Edit
            </TabsTrigger>
            <TabsTrigger value="preview" className="flex items-center gap-1">
              <Eye className="h-4 w-4" />
              Preview
            </TabsTrigger>
          </TabsList>
          
          {/* AI Assistant Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={toggleAssistantPanel}
            className="flex items-center gap-1"
          >
            <BrainCircuit className="h-4 w-4" />
            AI Assistant
          </Button>
        </div>

        <TabsContent value="edit" className="space-y-2">
          {/* Toolbar */}
          <div className="flex flex-wrap items-center gap-1 p-1 border rounded-md bg-muted/30">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.bold} 
              title="Bold"
              className="h-8 w-8"
            >
              <Bold className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.italic} 
              title="Italic"
              className="h-8 w-8"
            >
              <Italic className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.link} 
              title="Link"
              className="h-8 w-8"
            >
              <Link className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.listBullet} 
              title="Bullet List"
              className="h-8 w-8"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.listOrdered} 
              title="Numbered List"
              className="h-8 w-8"
            >
              <ListOrdered className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.heading1} 
              title="Heading 1"
              className="h-8 w-8"
            >
              <Heading1 className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.heading2} 
              title="Heading 2"
              className="h-8 w-8"
            >
              <Heading2 className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.code} 
              title="Code Block"
              className="h-8 w-8"
            >
              <Code className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.quote} 
              title="Quote"
              className="h-8 w-8"
            >
              <Quote className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={actions.table} 
              title="Table"
              className="h-8 w-8"
            >
              <Table className="h-4 w-4" />
            </Button>

            <DropdownMenu open={showImageDropdown} onOpenChange={setShowImageDropdown}>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  title="Insert Image"
                  className="h-8 w-8"
                >
                  <ImageIcon className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium mb-1.5">Image Alignment</p>
                  <div className="flex items-center gap-2 mb-2">
                    <Button 
                      variant={imageAlignment === 'left' ? 'default' : 'outline'} 
                      size="icon" 
                      className="h-8 w-8" 
                      onClick={() => setImageAlignment('left')}
                    >
                      <AlignLeft className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant={imageAlignment === 'center' ? 'default' : 'outline'} 
                      size="icon" 
                      className="h-8 w-8" 
                      onClick={() => setImageAlignment('center')}
                    >
                      <AlignCenter className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant={imageAlignment === 'right' ? 'default' : 'outline'} 
                      size="icon" 
                      className="h-8 w-8" 
                      onClick={() => setImageAlignment('right')}
                    >
                      <AlignRight className="h-4 w-4" />
                    </Button>
                  </div>

                  <p className="text-sm font-medium mb-1.5">Image Size</p>
                  <div className="flex items-center gap-2 mb-2">
                    <Button 
                      variant={imageSize === 'small' ? 'default' : 'outline'} 
                      size="sm" 
                      className="text-xs h-7 px-2" 
                      onClick={() => setImageSize('small')}
                    >
                      Small
                    </Button>
                    <Button 
                      variant={imageSize === 'medium' ? 'default' : 'outline'} 
                      size="sm" 
                      className="text-xs h-7 px-2" 
                      onClick={() => setImageSize('medium')}
                    >
                      Medium
                    </Button>
                    <Button 
                      variant={imageSize === 'large' ? 'default' : 'outline'} 
                      size="sm" 
                      className="text-xs h-7 px-2" 
                      onClick={() => setImageSize('large')}
                    >
                      Large
                    </Button>
                  </div>

                  <DropdownMenuSeparator className="my-2" />
                  <ImageUpload onImageUploaded={handleImageUploaded} />
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Editor */}
          <Textarea
            ref={textareaRef}
            placeholder={placeholder || "Start writing with markdown..."}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="min-h-[300px] font-mono text-sm"
          />
        </TabsContent>
        <TabsContent value="preview" className="space-y-2">
          {/* Preview */}
          <Card>
            <CardContent className="p-4 prose max-w-none">
              {value.trim() ? (
                <div dangerouslySetInnerHTML={{ __html: renderedHTML }} />
              ) : (
                <div className="text-muted-foreground italic">Nothing to preview...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* AI Assistant Panel */}
      <AIAssistantPanel 
        isOpen={isAssistantOpen} 
        onClose={toggleAssistantPanel}
        onInsertContent={handleInsertFromAssistant}
      />
    </div>
  );
} 