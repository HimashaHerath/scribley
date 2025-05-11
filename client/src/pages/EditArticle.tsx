import { useParams, Navigate } from 'react-router-dom';
import ArticleForm from '@/components/articles/ArticleForm';
import { useFetch } from '@/lib/hooks';
import { articleService } from '@/lib/api';

export default function EditArticle() {
  const { id } = useParams<{ id: string }>();
  
  const { data: article, isLoading, error } = useFetch(
    () => id ? articleService.getById(id) : Promise.reject('No article ID'),
    [id]
  );
  
  if (isLoading) {
    return <div className="p-8 text-center">Loading article...</div>;
  }
  
  if (error || !id || !article) {
    return <Navigate to="/articles" replace />;
  }
  
  return <ArticleForm article={article} isEditing />;
} 