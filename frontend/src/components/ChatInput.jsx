import React, { useState, useRef, useEffect } from 'react';
import { Send, Eraser, Sparkles, Loader2, CornerDownLeft } from 'lucide-react';

export default function ChatInput({
  onSendMessage,
  isLoading = false,
  placeholder = 'Enter a claim to verify in English or Indic languages...',
  initialValue = '',
}) {
  const [text, setText] = useState(initialValue);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (initialValue) {
      setText(initialValue);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [initialValue]);

  // Adjust textarea height dynamically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  const isDisabled = !text.trim() || isLoading;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      <div className="relative rounded-2xl bg-dark-900/90 border border-slate-700/60 shadow-glass focus-within:border-blue-500/60 focus-within:ring-1 focus-within:ring-blue-500/30 transition-all">
        {/* Top bar inside input */}
        <div className="flex items-center justify-between px-4 pt-2.5 text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5 text-blue-400">
            <Sparkles className="w-3.5 h-3.5" />
            <span className="font-sans font-medium">MuRIL Factual Verification</span>
          </div>
          <div className="flex items-center gap-3">
            <span>{text.length} chars</span>
            <span className="hidden sm:inline-block">•</span>
            <span className="hidden sm:inline-block text-slate-400">
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">Enter</kbd> to submit
            </span>
          </div>
        </div>

        {/* Textarea Input */}
        <form onSubmit={handleSubmit} className="p-3 pt-1.5 flex items-end gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder={placeholder}
            className="w-full resize-none bg-transparent px-2 py-1.5 text-sm text-slate-100 placeholder-slate-400 focus:outline-none disabled:opacity-50 min-h-[44px] max-h-[180px] font-sans leading-relaxed"
          />

          {/* Action Buttons */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {text.trim() && !isLoading && (
              <button
                type="button"
                onClick={handleClear}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                title="Clear input"
                aria-label="Clear claim text"
              >
                <Eraser className="w-4 h-4" />
              </button>
            )}

            <button
              type="submit"
              disabled={isDisabled}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold font-mono tracking-wide transition-all shadow-md ${
                isDisabled
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700/50'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-glow-blue border border-blue-400/30 active:scale-95'
              }`}
              title={isLoading ? 'Verification running...' : 'Submit claim for verification'}
              aria-label="Verify claim"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-blue-300" />
                  <span className="hidden sm:inline">Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Verify</span>
                  <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <div className="mt-2 text-center text-[11px] text-slate-400 font-sans">
        IndicClaimVer searches 50k+ multilingual evidence records and classifies factuality with fine-tuned MuRIL.
      </div>
    </div>
  );
}
