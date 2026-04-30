import { Badge } from "rizzui/badge";
import { Title, Text } from "rizzui/typography";

interface Props {
  title: string;
  reference: string;
  date: string;
  slot: string;
  href: string;
  imageUrl?: string;
}

export default function DevotionalCard({
  title,
  reference,
  date,
  slot,
  href,
  imageUrl,
}: Props) {
  return (
    <a
      href={href}
      className="block rounded-xl border p-4 transition-colors hover:bg-(--muted)"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex flex-col gap-3 sm:flex-row">
        {imageUrl && (
          <img
            src={imageUrl}
            alt=""
            className="h-32 w-full rounded-lg object-cover sm:h-24 sm:w-36"
            loading="lazy"
          />
        )}
        <div className="flex flex-1 flex-col gap-1">
          <div className="flex items-center gap-2">
            <Badge variant="flat" size="sm">
              {slot}
            </Badge>
            <Text className="!text-xs" style={{ color: "var(--muted-foreground)" }}>
              {date} · {reference}
            </Text>
          </div>
          <Title as="h3" className="!text-base !font-semibold">
            {title}
          </Title>
        </div>
      </div>
    </a>
  );
}
