function LoadingSpinner() {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-500">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      <span>Loading...</span>
    </div>
  );
}

export default LoadingSpinner;
