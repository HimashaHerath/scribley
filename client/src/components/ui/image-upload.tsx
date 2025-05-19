import { useState, useRef } from 'react';
import { Button } from './button';
import { Input } from './input';
import { UploadCloud, X, Image as ImageIcon, Loader2, AlertCircle } from 'lucide-react';
import { articleService } from '@/lib/api';
import { toast } from 'sonner';

interface ImageUploadProps {
  onImageUploaded: (imageUrl: string) => void;
  className?: string;
}

export function ImageUpload({ onImageUploaded, className }: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file: File): boolean => {
    // Clear previous error
    setErrorMessage(null);
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setErrorMessage('Please upload a valid image file (JPEG, PNG, GIF)');
      return false;
    }
    
    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setErrorMessage(`Image size must be less than 5MB (current size: ${(file.size / (1024 * 1024)).toFixed(2)}MB)`);
      return false;
    }
    
    return true;
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        await handleUpload(file);
      } else {
        toast.error(errorMessage || 'Invalid file');
      }
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        await handleUpload(file);
      } else {
        toast.error(errorMessage || 'Invalid file');
      }
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    
    try {
      const result = await articleService.uploadImage(file);
      if (result && result.url) {
        onImageUploaded(result.url);
        toast.success('Image uploaded successfully');
      } else {
        throw new Error('Upload response missing image URL');
      }
    } catch (error) {
      console.error('Image upload failed:', error);
      let message = 'Failed to upload image. Please try again.';
      
      if (error instanceof Error) {
        message = `Upload failed: ${error.message}`;
      }
      
      toast.error(message);
      setErrorMessage(message);
    } finally {
      setIsUploading(false);
      // Reset the input
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    }
  };

  const onButtonClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };

  return (
    <div className={`relative ${className}`}>
      <div 
        className={`
          flex flex-col items-center justify-center w-full h-32
          border-2 border-dashed rounded-md
          ${errorMessage ? 'border-destructive bg-destructive/5' : 
            dragActive ? 'border-primary bg-primary/5' : 'border-border'}
          transition-colors duration-200
          hover:bg-muted/50
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <Input
          ref={inputRef}
          type="file"
          onChange={handleChange}
          accept="image/jpeg,image/png,image/gif"
          className="hidden"
        />
        
        {isUploading ? (
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
            <p className="text-sm text-muted-foreground">Uploading...</p>
          </div>
        ) : errorMessage ? (
          <div className="flex flex-col items-center gap-2 p-2">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <p className="text-sm text-destructive text-center">
              {errorMessage}
            </p>
            <Button variant="outline" size="sm" onClick={() => setErrorMessage(null)}>
              Try Again
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <UploadCloud className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Drag & drop an image or <Button variant="link" onClick={onButtonClick} className="py-0 h-auto">browse</Button>
            </p>
            <p className="text-xs text-muted-foreground">
              Supported formats: JPEG, PNG, GIF (max 5MB)
            </p>
          </div>
        )}
      </div>
    </div>
  );
} 