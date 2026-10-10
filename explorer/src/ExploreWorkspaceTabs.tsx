export type ExploreView = 'graph' | 'memories' | 'vocabulary';

type ExploreWorkspaceTabsProps = {
  activeView: ExploreView;
  agentMemoryAvailable: boolean;
  onSelect: (view: ExploreView) => void;
};

export function ExploreWorkspaceTabs({
  activeView,
  agentMemoryAvailable,
  onSelect,
}: ExploreWorkspaceTabsProps) {
  const { tr } = useI18n();
  return (
    <>
      <button className="workspace-tab" data-active={activeView === 'graph'} onClick={() => onSelect('graph')}>
        {tr("Semantica Explorer")}
      </button>
      {agentMemoryAvailable ? (
        <button className="workspace-tab" data-active={activeView === 'memories'} onClick={() => onSelect('memories')}>
          {tr("Memories")}
        </button>
      ) : null}
      <button className="workspace-tab" data-active={activeView === 'vocabulary'} onClick={() => onSelect('vocabulary')}>
        {tr("Vocabulary Browser")}
      </button>
    </>
  );
}
import { useI18n } from "./i18n";
