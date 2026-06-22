import { useState, useEffect, useRef } from 'react';
import { X, Bell } from 'lucide-react';

interface SubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SubscriptionModal({ isOpen, onClose }: SubscriptionModalProps) {
  const [email, setEmail] = useState('');
  const [keywords, setKeywords] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // 在实际场景中，这里会调用 API 保存订阅
    setSubscribed(true);
    setTimeout(() => {
      onClose();
      setSubscribed(false);
      setEmail('');
      setKeywords('');
    }, 2000);
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div className="modal-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="modal-content">
        <div className="modal-header">
          <div className="modal-header-info">
            <h2 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Bell size={20} /> 订阅校招推送
            </h2>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="关闭">
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {subscribed ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
              <h3 style={{ fontWeight: 600, marginBottom: 8 }}>订阅成功！</h3>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
                我们会将最新的校招信息推送到你的邮箱
              </p>
            </div>
          ) : (
            <form className="subscription-form" onSubmit={handleSubmit}>
              <div className="subscription-form-group">
                <label className="subscription-form-label">邮箱地址</label>
                <input
                  className="subscription-form-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                />
              </div>

              <div className="subscription-form-group">
                <label className="subscription-form-label">关注的关键词（逗号分隔）</label>
                <input
                  className="subscription-form-input"
                  type="text"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  placeholder="如：产品经理, 字节跳动, 北京"
                />
                <span className="subscription-form-hint">
                  有匹配的新职位时将第一时间通知你
                </span>
              </div>

              <button type="submit" className="btn btn-primary" style={{ marginTop: 8 }}>
                <Bell size={16} />
                确认订阅
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
