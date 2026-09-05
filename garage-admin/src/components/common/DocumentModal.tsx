import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useSendDocument } from "@/lib/queries/documents"
import { toast } from "sonner"

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  doctype: string
  name: string
}

export function DocumentModal({ open, onOpenChange, doctype, name }: Props) {
  const [email, setEmail] = useState("")
  const send = useSendDocument()

  const handlePrint = async () => {
    try {
      const res = await send.mutateAsync({ doctype, name, channel: "print" })
      // open html in new window
      const w = window.open("", "_blank")
      if (w && res.html) {
        w.document.write(res.html as string)
        w.document.close()
        w.print()
      }
      toast.success("Print ready")
    } catch {
      toast.error("Print failed")
    }
  }

  const handlePdf = async () => {
    try {
      await send.mutateAsync({ doctype, name, channel: "pdf" })
      toast.success("PDF downloaded")
    } catch {
      toast.error("PDF failed")
    }
  }

  const handleEmail = async () => {
    try {
      await send.mutateAsync({ doctype, name, channel: "email", recipient: email })
      toast.success(`Emailed to ${email}`)
    } catch {
      toast.error("Email failed")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="document-modal">
        <DialogHeader>
          <DialogTitle>
            {doctype} {name}
          </DialogTitle>
          <DialogDescription>Preview and send this document</DialogDescription>
        </DialogHeader>
        <div className="flex gap-2">
          <Button onClick={handlePrint} data-testid="doc-print">Print</Button>
          <Button variant="outline" onClick={handlePdf} data-testid="doc-pdf">
            Download PDF
          </Button>
        </div>
        <div className="flex gap-2 items-end pt-4 border-t">
          <div className="flex-1">
            <label className="text-sm font-medium">Email to</label>
            <Input placeholder="customer@example.com" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="doc-email-input" />
          </div>
          <Button onClick={handleEmail} disabled={!email} data-testid="doc-email">
            Email
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
