import { useTheme } from "next-themes"
import { Toaster as Sonner, toast } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

// Custom functions for persistent toasts
export const showWarning = (
  message: string, 
  title?: string, 
  options?: { 
    duration?: number, 
    onDismiss?: () => void,
    action?: { label: string, onClick: () => void }
  }
) => {
  return toast.warning(
    <div>
      {title && <div className="font-medium">{title}</div>}
      <div>{message}</div>
    </div>,
    {
      duration: options?.duration || Infinity,
      action: options?.action ? {
        label: options.action.label,
        onClick: options.action.onClick
      } : undefined,
      onDismiss: options?.onDismiss,
      className: "bg-amber-50 border-amber-200 text-amber-800"
    }
  );
};

export const showInfo = (
  message: string, 
  title?: string, 
  options?: { 
    duration?: number, 
    onDismiss?: () => void,
    action?: { label: string, onClick: () => void }
  }
) => {
  return toast.info(
    <div>
      {title && <div className="font-medium">{title}</div>}
      <div>{message}</div>
    </div>,
    {
      duration: options?.duration || Infinity,
      action: options?.action ? {
        label: options.action.label,
        onClick: options.action.onClick
      } : undefined,
      onDismiss: options?.onDismiss,
      className: "bg-blue-50 border-blue-200 text-blue-800"
    }
  );
};

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as "light" | "dark" | "system"}
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      closeButton
      {...props}
    />
  )
}

export { Toaster, toast }
