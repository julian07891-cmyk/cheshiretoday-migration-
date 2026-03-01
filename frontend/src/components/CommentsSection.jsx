import React, { useState, useEffect, useCallback } from 'react';
import { MessageSquare, ThumbsUp, Reply, Trash2, Send, LogOut, Mail, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { getApiUrl } from '../utils/api';
const API_URL = getApiUrl();
// CommentItem component - defined outside to avoid re-creation on each render
const CommentItem = ({ 
  comment, 
  isReply = false, 
  user, 
  replyTo, 
  setReplyTo, 
  replyContent, 
  setReplyContent, 
  submitting,
  handleLike, 
  handleDelete, 
  handleSubmitReply,
  formatDate 
}) => (
  <div className={`${isReply ? 'ml-8 mt-3' : ''} p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg`}>
    <div className="flex items-start justify-between">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-[#1E3A8A] flex items-center justify-center text-white text-sm font-bold">
          {comment.user_name?.charAt(0).toUpperCase()}
        </div>
        <div>
          <span className="font-semibold text-gray-900 dark:text-white text-sm">
            {comment.user_name}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
            {formatDate(comment.created_at)}
          </span>
        </div>
      </div>
      {user && user.user_id === comment.user_id && (
        <button
          onClick={() => handleDelete(comment.id)}
          className="text-gray-400 hover:text-red-500 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </div>
    
    <p className="mt-2 text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">
      {comment.content}
    </p>
    
    <div className="flex items-center gap-4 mt-3">
      <button
        onClick={() => handleLike(comment.id)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-[#1E3A8A] transition-colors"
      >
        <ThumbsUp className="h-4 w-4" />
        {comment.likes > 0 && <span>{comment.likes}</span>}
      </button>
      {!isReply && (
        <button
          onClick={() => setReplyTo(replyTo === comment.id ? null : comment.id)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-[#1E3A8A] transition-colors"
        >
          <Reply className="h-4 w-4" />
          Reply
        </button>
      )}
    </div>
    
    {/* Reply input */}
    {replyTo === comment.id && user && (
      <div className="mt-3 flex gap-2">
        <Input
          value={replyContent}
          onChange={(e) => setReplyContent(e.target.value)}
          placeholder="Write a reply..."
          className="flex-1 text-sm"
        />
        <Button
          size="sm"
          onClick={() => handleSubmitReply(comment.id)}
          disabled={submitting || !replyContent.trim()}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    )}
    
    {/* Replies */}
    {comment.replies?.map((reply) => (
      <CommentItem 
        key={reply.id} 
        comment={reply} 
        isReply 
        user={user}
        replyTo={replyTo}
        setReplyTo={setReplyTo}
        replyContent={replyContent}
        setReplyContent={setReplyContent}
        submitting={submitting}
        handleLike={handleLike}
        handleDelete={handleDelete}
        handleSubmitReply={handleSubmitReply}
        formatDate={formatDate}
      />
    ))}
  </div>
);

const CommentsSection = ({ articleId }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [showLogin, setShowLogin] = useState(false);
  const [loginStep, setLoginStep] = useState('email'); // 'email' or 'verify'
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [replyContent, setReplyContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fetchComments = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/comments/article/${articleId}`);
      const data = await response.json();
      if (data.success) {
        setComments(data.comments);
      }
    } catch (e) {
      console.error('Failed to fetch comments:', e);
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  // Check for existing session
  useEffect(() => {
    const token = localStorage.getItem('comment_token');
    if (token) {
      checkSession(token);
    }
    fetchComments();
  }, [articleId, fetchComments]);

  const checkSession = async (token) => {
    try {
      const response = await fetch(`${API_URL}/api/comments/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        localStorage.removeItem('comment_token');
      }
    } catch (e) {
      console.error('Session check failed:', e);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    try {
      const response = await fetch(`${API_URL}/api/comments/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name })
      });
      const data = await response.json();
      
      if (response.ok) {
        setLoginStep('verify');
      } else {
        setError(data.detail || 'Failed to send verification code');
      }
    } catch (e) {
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    try {
      const response = await fetch(`${API_URL}/api/comments/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code: verificationCode })
      });
      const data = await response.json();
      
      if (response.ok && data.success) {
        localStorage.setItem('comment_token', data.token);
        setUser(data.user);
        setShowLogin(false);
        setLoginStep('email');
        setEmail('');
        setName('');
        setVerificationCode('');
      } else {
        setError(data.detail || 'Invalid verification code');
      }
    } catch (e) {
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('comment_token');
    if (token) {
      await fetch(`${API_URL}/api/comments/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    localStorage.removeItem('comment_token');
    setUser(null);
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    
    setSubmitting(true);
    const token = localStorage.getItem('comment_token');
    
    try {
      const response = await fetch(`${API_URL}/api/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          article_id: articleId,
          content: newComment,
          parent_id: null
        })
      });
      
      if (response.ok) {
        setNewComment('');
        fetchComments();
      }
    } catch (e) {
      console.error('Failed to post comment:', e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitReply = async (parentId) => {
    if (!replyContent.trim()) return;
    
    setSubmitting(true);
    const token = localStorage.getItem('comment_token');
    
    try {
      const response = await fetch(`${API_URL}/api/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          article_id: articleId,
          content: replyContent,
          parent_id: parentId
        })
      });
      
      if (response.ok) {
        setReplyContent('');
        setReplyTo(null);
        fetchComments();
      }
    } catch (e) {
      console.error('Failed to post reply:', e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleLike = async (commentId) => {
    const token = localStorage.getItem('comment_token');
    if (!token) {
      setShowLogin(true);
      return;
    }
    
    try {
      await fetch(`${API_URL}/api/comments/${commentId}/like`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchComments();
    } catch (e) {
      console.error('Failed to like:', e);
    }
  };

  const handleDelete = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;
    
    const token = localStorage.getItem('comment_token');
    try {
      await fetch(`${API_URL}/api/comments/${commentId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchComments();
    } catch (e) {
      console.error('Failed to delete:', e);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  };

  return (
    <div className="mt-6" data-testid="comments-section">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-headline text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Comments {comments.length > 0 && `(${comments.length})`}
        </h3>
        
        {user ? (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {user.name}
            </Badge>
            <button
              onClick={handleLogout}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowLogin(true)}
            className="text-[#1E3A8A] border-[#1E3A8A]"
          >
            <Mail className="h-4 w-4 mr-1" />
            Login to Comment
          </Button>
        )}
      </div>
      
      {/* Login Modal */}
      {showLogin && !user && (
        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
            {loginStep === 'email' ? 'Login with Email' : 'Enter Verification Code'}
          </h4>
          
          {error && (
            <p className="text-red-600 text-sm mb-3">{error}</p>
          )}
          
          {loginStep === 'email' ? (
            <form onSubmit={handleRegister} className="space-y-3">
              <div>
                <Input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  minLength={2}
                />
              </div>
              <div>
                <Input
                  type="email"
                  placeholder="Your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={submitting} className="bg-[#1E3A8A]">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Send Code'}
                </Button>
                <Button type="button" variant="ghost" onClick={() => setShowLogin(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleVerify} className="space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                We&apos;ve sent a 6-digit code to <strong>{email}</strong>
              </p>
              <div>
                <Input
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  maxLength={6}
                  className="text-center text-2xl tracking-widest"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={submitting || verificationCode.length !== 6} className="bg-[#1E3A8A]">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Verify'}
                </Button>
                <Button type="button" variant="ghost" onClick={() => setLoginStep('email')}>
                  Back
                </Button>
              </div>
            </form>
          )}
        </div>
      )}
      
      {/* New Comment Form */}
      {user && (
        <form onSubmit={handleSubmitComment} className="mb-4">
          <Textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Share your thoughts..."
            className="mb-2"
            rows={3}
          />
          <Button
            type="submit"
            disabled={submitting || !newComment.trim()}
            className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
            Post Comment
          </Button>
        </form>
      )}
      
      <Separator className="my-4" />
      
      {/* Comments List */}
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      ) : comments.length === 0 ? (
        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
          No comments yet. Be the first to share your thoughts!
        </p>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <CommentItem 
              key={comment.id} 
              comment={comment}
              user={user}
              replyTo={replyTo}
              setReplyTo={setReplyTo}
              replyContent={replyContent}
              setReplyContent={setReplyContent}
              submitting={submitting}
              handleLike={handleLike}
              handleDelete={handleDelete}
              handleSubmitReply={handleSubmitReply}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default CommentsSection;
