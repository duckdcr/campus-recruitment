import { useEffect, useRef } from 'react';
import { X, MapPin, Briefcase, GraduationCap, Clock, Building2, ExternalLink } from 'lucide-react';
import type { Job } from '../types/job';
import { formatFullDate } from '../utils';

interface JobDetailModalProps {
  job: Job;
  onClose: () => void;
}

export function JobDetailModal({ job, onClose }: JobDetailModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // 点击蒙层关闭
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (e.target === overlayRef.current) onClose();
    };
    const overlay = overlayRef.current;
    overlay?.addEventListener('click', handleClick);
    return () => overlay?.removeEventListener('click', handleClick);
  }, [onClose]);

  // ESC 关闭
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // 锁定 body 滚动
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return (
    <div className="modal-overlay" ref={overlayRef}>
      <div className="modal-content">
        <div className="modal-header">
          <div className="modal-header-info">
            <h2 className="modal-title">{job.title}</h2>
            <div className="modal-company">{job.company}</div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="关闭">
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* 基本信息 */}
          <div className="modal-meta">
            <span className="modal-meta-item">
              <Briefcase size={14} />
              {job.salary}
            </span>
            <span className="modal-meta-item">
              <MapPin size={14} />
              {job.city}
            </span>
            <span className="modal-meta-item">
              <GraduationCap size={14} />
              {job.education}
            </span>
            <span className="modal-meta-item">
              <Clock size={14} />
              发布：{formatFullDate(job.postedAt)}
            </span>
            {job.deadline && (
              <span className="modal-meta-item">
                <Clock size={14} />
                截止：{formatFullDate(job.deadline)}
              </span>
            )}
            <span className="modal-meta-item">
              <Building2 size={14} />
              {job.industry}
            </span>
          </div>

          {/* 职位描述 */}
          <div className="modal-section">
            <h3 className="modal-section-title">职位描述</h3>
            <p className="modal-section-text">{job.description}</p>
          </div>

          {/* 职位要求 */}
          <div className="modal-section">
            <h3 className="modal-section-title">任职要求</h3>
            <ul className="modal-requirement-list">
              {job.requirements.map((req, idx) => (
                <li key={idx}>{req}</li>
              ))}
            </ul>
          </div>

          {/* 标签 */}
          <div className="modal-section">
            <h3 className="modal-section-title">标签</h3>
            <div className="filter-chip-group">
              {job.tags.map((tag) => (
                <span key={tag} className="filter-chip" style={{ cursor: 'default' }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="modal-actions">
            <a
              href={job.applyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              立即投递
              <ExternalLink size={16} />
            </a>
            <button className="btn btn-outline" onClick={onClose}>
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
