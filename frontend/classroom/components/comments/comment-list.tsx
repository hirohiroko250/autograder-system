'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MessageSquare, Edit2, Trash2, Save, X, Clock, User } from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { toast } from 'sonner';

interface Comment {
  id: string;
  content: string;
  comment_type: string;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  student_name?: string;
  test_name?: string;
}

interface CommentListProps {
  comments: Comment[];
  onEdit?: (commentId: string, data: { content: string; comment_type: string }) => Promise<void>;
  onDelete?: (commentId: string) => Promise<void>;
  isLoading?: boolean;
  showStudentName?: boolean;
  showTestName?: boolean;
  filterByType?: string;
}

const COMMENT_TYPES = [
  { value: 'general', label: '総合コメント', color: 'bg-blue-100 text-blue-800' },
  { value: 'improvement', label: '改善点', color: 'bg-orange-100 text-orange-800' },
  { value: 'strength', label: '強み', color: 'bg-green-100 text-green-800' },
  { value: 'homework', label: '宿題・課題', color: 'bg-purple-100 text-purple-800' },
  { value: 'parent_note', label: '保護者連絡', color: 'bg-pink-100 text-pink-800' },
  { value: 'behavioral', label: '学習態度', color: 'bg-indigo-100 text-indigo-800' },
  { value: 'academic', label: '学習内容', color: 'bg-yellow-100 text-yellow-800' },
];

export function CommentList({ 
  comments, 
  onEdit, 
  onDelete, 
  isLoading = false,
  showStudentName = false,
  showTestName = false,
  filterByType
}: CommentListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editType, setEditType] = useState('');
  const [typeFilter, setTypeFilter] = useState(filterByType || 'all');

  const getTypeInfo = (type: string) => {
    return COMMENT_TYPES.find(t => t.value === type) || COMMENT_TYPES[0];
  };

  const handleEditStart = (comment: Comment) => {
    setEditingId(comment.id);
    setEditContent(comment.content);
    setEditType(comment.comment_type);
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditContent('');
    setEditType('');
  };

  const handleEditSave = async (commentId: string) => {
    if (!onEdit) return;

    try {
      await onEdit(commentId, {
        content: editContent,
        comment_type: editType
      });
      setEditingId(null);
      setEditContent('');
      setEditType('');
      toast.success('コメントを更新しました');
    } catch (error) {
      console.error('Error updating comment:', error);
      toast.error('コメントの更新に失敗しました');
    }
  };

  const handleDelete = async (commentId: string) => {
    if (!onDelete) return;

    if (!confirm('このコメントを削除しますか？')) return;

    try {
      await onDelete(commentId);
      toast.success('コメントを削除しました');
    } catch (error) {
      console.error('Error deleting comment:', error);
      toast.error('コメントの削除に失敗しました');
    }
  };

  const filteredComments = comments.filter(comment => 
    typeFilter === 'all' || comment.comment_type === typeFilter
  );

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            コメントを読み込み中...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              コメント一覧 ({filteredComments.length}件)
            </CardTitle>
            
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="タイプで絞り込み" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">すべてのタイプ</SelectItem>
                {COMMENT_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${type.color}`} />
                      {type.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
      </Card>

      {filteredComments.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>コメントがありません</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredComments.map((comment) => {
            const typeInfo = getTypeInfo(comment.comment_type);
            const isEditing = editingId === comment.id;

            return (
              <Card key={comment.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={typeInfo.color} variant="secondary">
                          {typeInfo.label}
                        </Badge>
                        
                        {showStudentName && comment.student_name && (
                          <Badge variant="outline">
                            <User className="h-3 w-3 mr-1" />
                            {comment.student_name}
                          </Badge>
                        )}
                        
                        {showTestName && comment.test_name && (
                          <Badge variant="outline">
                            {comment.test_name}
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {onEdit && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditStart(comment)}
                            disabled={isEditing}
                          >
                            <Edit2 className="h-3 w-3" />
                          </Button>
                        )}
                        {onDelete && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(comment.id)}
                            disabled={isEditing}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {isEditing ? (
                      <div className="space-y-3">
                        <Select value={editType} onValueChange={setEditType}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {COMMENT_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                <div className="flex items-center gap-2">
                                  <div className={`w-3 h-3 rounded-full ${type.color}`} />
                                  {type.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        
                        <Textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="min-h-24"
                        />
                        
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={handleEditCancel}
                          >
                            <X className="h-3 w-3 mr-1" />
                            キャンセル
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleEditSave(comment.id)}
                          >
                            <Save className="h-3 w-3 mr-1" />
                            保存
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="prose prose-sm max-w-none">
                        <p className="whitespace-pre-wrap">{comment.content}</p>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-muted-foreground border-t pt-2">
                      <div className="flex items-center gap-1">
                        <Avatar className="h-4 w-4">
                          <AvatarFallback className="text-xs">
                            {comment.created_by_name?.charAt(0) || 'U'}
                          </AvatarFallback>
                        </Avatar>
                        <span>{comment.created_by_name || '不明'}</span>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>
                          {format(new Date(comment.created_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
                        </span>
                      </div>
                      
                      {comment.updated_at !== comment.created_at && (
                        <span className="text-orange-600">
                          (更新: {format(new Date(comment.updated_at), 'MM/dd HH:mm', { locale: ja })})
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}