import { useMutation } from "@tanstack/react-query"
import { call } from "../frappe-client"

export const useSendDocument = () =>
  useMutation({
    mutationFn: ({
      doctype,
      name,
      channel,
      recipient,
    }: {
      doctype: string
      name: string
      channel: "print" | "email" | "pdf"
      recipient?: string
    }) => call.post("subamaz.api.documents.send_document", { doctype, name, channel, recipient }),
  })
